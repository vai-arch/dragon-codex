"""
Embed All Chunks - FIXED VERSION with Per-Batch Checkpointing

This version saves progress every 100 chunks, not just per file.
You can stop at ANY TIME and resume with minimal progress loss.

Features:
- Checkpoint every 100 chunks (max 7 minutes lost work)
- Resume from exact position
- Progress tracking with ETA
- Safe for 30-hour runs
- Uses config.py for all paths

Usage:
    python embed_all_chunks_v2.py           # Start or resume
    python embed_all_chunks_v2.py --reset   # Start fresh
"""

import json
import os
import pickle
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from tqdm import tqdm

from src.utils.paths import get_paths
from src.utils.util_embedding import VectorStoreManager
from src.utils.util_files_functions import get_object_size_mb, load_json_line_by_line, remove_file, serialize_object
from src.utils.util_statistics import (
    log_processed_time,
    log_results,
    log_results_table,
    print_processed_time,
    print_results_table,
    reset_log,
)

in_files_to_embed = None
out_embedding_path = None
aux_partial_results_paths_map = None
aux_file_embedding_checklpoint = None


class ImprovedCheckpoint:
    """Enhanced checkpoint with per-batch progress tracking"""

    def __init__(self):
        self.checkpoint_file = str(aux_file_embedding_checklpoint)
        self.state = self._load_checkpoint()

    def _load_checkpoint(self) -> Dict:
        """Load checkpoint or create new"""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, "r") as f:
                return json.load(f)
        else:
            return {
                "current_file": None,
                "current_file_progress": 0,  # Chunks completed in current file
                "completed_files": [],
                "total_chunks_embedded": 0,
                "total_time_seconds": 0,
                "started_at": None,
                "last_updated": None,
            }

    def save_checkpoint(self):
        """Save current state"""
        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)
        self.state["last_updated"] = datetime.now().isoformat()

        with open(self.checkpoint_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def start_file(self, filename: str):
        """Mark start of processing a file"""
        if self.state["current_file"] != filename:
            # Starting new file
            self.state["current_file"] = filename
            self.state["current_file_progress"] = 0
        # else: resuming same file from checkpoint

        if self.state["started_at"] is None:
            self.state["started_at"] = datetime.now().isoformat()

        self.save_checkpoint()

    def update_progress(self, chunks_completed: int, elapsed_seconds: float):
        """Update progress (called every batch)"""
        self.state["current_file_progress"] = chunks_completed
        self.state["total_chunks_embedded"] = chunks_completed  # Use actual count
        self.state["total_time_seconds"] = elapsed_seconds  # Use cumulative time
        self.save_checkpoint()

    def complete_file(self, filename: str):
        """Mark file as completed"""
        if filename not in self.state["completed_files"]:
            self.state["completed_files"].append(filename)

        self.state["current_file"] = None
        self.state["current_file_progress"] = 0
        self.save_checkpoint()

    def is_file_completed(self, filename: str) -> bool:
        """Check if file already completed"""
        return filename in self.state["completed_files"]

    def get_file_progress(self, filename: str) -> int:
        """Get progress in current file (0 if not started or completed)"""
        if self.is_file_completed(filename):
            return -1  # Fully done

        if self.state["current_file"] == filename:
            return self.state["current_file_progress"]

        return 0  # Not started

    def reset(self):
        """Reset checkpoint (start fresh)"""
        self.state = {
            "current_file": None,
            "current_file_progress": 0,
            "completed_files": [],
            "total_chunks_embedded": 0,
            "total_time_seconds": 0,
            "started_at": None,
            "last_updated": None,
        }
        self.save_checkpoint()
        print("✅ Checkpoint reset. Starting fresh.")


def embed_file_resumable(
    source_path: Path,
    output_path: str,
    manager: VectorStoreManager,
    checkpoint: ImprovedCheckpoint,
    batch_size: int = 100,
) -> Tuple[int, float]:
    """
    Embed chunks from file with batch processing and per-batch checkpointing

    Can resume from last checkpoint position (aligned to batch boundaries)

    Args:
        source_path: Path to .jsonl file with chunks
        output_path: Path to save embeddings .pkl file
        manager: VectorStoreManager instance
        checkpoint: ImprovedCheckpoint instance
        config: Config instance
        batch_size: Number of chunks to embed per API call

    Returns:
        Tuple[int, float]: (chunk_count, elapsed_seconds)
    """

    # batch_size = 2

    filename = source_path.name
    temp_path = str(aux_partial_results_paths_map.get(source_path.stem))

    print(f"\n{'=' * 70}")
    print(f"Embedding: {filename}")
    print(f"Output: {os.path.basename(output_path)}")
    print(f"{'=' * 70}\n")

    # Load chunks
    chunks = load_json_line_by_line(source_path)

    # Check for resume
    start_from = checkpoint.get_file_progress(filename)

    if start_from == -1:
        print("✅ File already completed, skipping")
        return 0, 0

    # Align start position to batch boundary
    start_from = (start_from // batch_size) * batch_size

    # Load partial progress if resuming
    embeddings_data = {}
    if start_from > 0 and os.path.exists(temp_path):
        print(f"📂 Resuming from chunk {start_from} (batch boundary)")
        with open(temp_path, "rb") as f:
            embeddings_data = pickle.load(f)
        print(f"   Loaded {len(embeddings_data)} existing embeddings")
    else:
        print("🆕 Starting fresh")
        start_from = 0

    # Mark start
    checkpoint.start_file(filename)

    # Get chunks to process
    chunks_to_process = chunks[start_from:]

    # chunks_to_process = chunks[:3]

    total_chunks = len(chunks_to_process)

    if not chunks_to_process:
        print("✅ No chunks to process")
        checkpoint.complete_file(filename)
        return 0, 0

    print(f"\nEmbedding {len(chunks_to_process)} chunks (batch size: {batch_size})...")
    print()

    total_time = 0
    max_tokens_used = 0
    avg_tokens = 0
    total_batches = (len(chunks_to_process) + batch_size - 1) // batch_size
    num_rounds = 0
    # Process in batches
    for batch_idx in tqdm(range(0, len(chunks_to_process), batch_size), desc="Embedding batches", total=total_batches):
        batch_chunks = chunks_to_process[batch_idx : batch_idx + batch_size]
        batch_texts = [chunk["text"] for chunk in batch_chunks]
        actual_start_idx = start_from + batch_idx
        num_rounds += 1

        try:
            batch_embeddings, batch_avg_tokens, max_tokens, batch_time = manager.embed_chunks(batch_texts, batch_size, False)

            total_time += batch_time.total_seconds()
            avg_tokens += batch_avg_tokens

            # Track max tokens
            if max_tokens > max_tokens_used:
                max_tokens_used = max_tokens
                print(f"\n   NEW MAX TOKENS USED: {max_tokens_used}")

            # Store embeddings with metadata
            for i, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                chunk_id = f"chunk_{actual_start_idx + i}"
                embeddings_data[chunk_id] = {
                    "embedding": embedding,
                    "text": chunk["text"],
                    "metadata": {k: v for k, v in chunk.items() if k != "text"},
                }

        except Exception as e:
            print(f"\n❌ ERROR on batch starting at chunk {actual_start_idx}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {e}")
            print(f"Batch size: {len(batch_texts)}")
            print(f"First chunk length: {len(batch_texts[0]) if batch_texts else 0}")

            # Could implement retry logic here
            raise  # Re-raise for now

        # Checkpoint after each batch
        # Save partial progress
        serialize_object(embeddings_data, temp_path)

        # Update checkpoint (position = end of this batch)
        completed = actual_start_idx + len(batch_chunks)
        checkpoint.update_progress(completed, total_time)

    statistics = {
        "name": filename,
        "metrics": {
            "total_chunks": total_chunks,
            "total_time": total_time,
            "avg_time": total_time / (batch_size * num_rounds),
            "avg_tokens": avg_tokens / num_rounds,
            "max_tokens": max_tokens,
        },
    }

    print_results_table(statistics, filename)
    # Final save to permanent location
    serialize_object(embeddings_data, output_path)

    # remove temporal object
    remove_file(temp_path)

    # Mark complete
    checkpoint.complete_file(filename)

    # Summary
    file_size_mb = get_object_size_mb(output_path)

    print("\n✅ Completed!")
    print(f"   Chunks embedded: {total_chunks}")
    print(f"   MAX TOKENS USED: {max_tokens_used}")
    print(f"   Time taken: {total_time / 60:.1f} minutes")
    print(f"   Rate: {total_chunks / total_time:.2f} chunks/second")
    print(f"   File size: {file_size_mb:.1f} MB")

    return statistics


def main(reset: bool = False):
    """Main embedding process"""

    start_time = datetime.now()

    # Initialize
    manager = VectorStoreManager()
    checkpoint = ImprovedCheckpoint()

    reset = True

    if reset:
        checkpoint.reset()

    # Check status
    pending_files = []
    completed_files = []
    current_file_info = None

    for filepath, expected_count, description in in_files_to_embed:
        filename = filepath.name

        output_path = str(out_embedding_path / f"{filepath.stem}.embeddings.pkl")

        progress = checkpoint.get_file_progress(filename)

        if progress == -1:
            # Completed
            completed_files.append((filename, expected_count, description))
        elif progress > 0:
            # In progress
            current_file_info = (filepath, filename, expected_count, description, progress, output_path)
        else:
            # Not started
            pending_files.append((filepath, expected_count, description, output_path))

    if checkpoint.state["started_at"]:
        print(f"Started: {checkpoint.state['started_at']}")
        print(f"Last updated: {checkpoint.state['last_updated']}")
        print()

    print(f"Total chunks embedded: {checkpoint.state['total_chunks_embedded']:,}")
    print(f"Total time: {checkpoint.state['total_time_seconds'] / 3600:.1f} hours")
    print()

    if completed_files:
        print(f"✅ Completed: {len(completed_files)} file(s)")
        for filename, count, desc in completed_files:
            print(f"   - {filename} ({count:,} chunks)")
        print()

    if current_file_info:
        filepath, filename, expected_count, description, progress, output_path = current_file_info
        remaining = expected_count - progress
        percent = (progress / expected_count) * 100

        print(f"⏳ IN PROGRESS: {filename}")
        print(f"   Progress: {progress:,}/{expected_count:,} ({percent:.1f}%)")
        print(f"   Remaining: {remaining:,} chunks")
        print()

    if pending_files:
        pending_chunks = sum(count for _, count, _, _ in pending_files)
        print(f"📋 Pending: {len(pending_files)} file(s)")
        print(f"   Remaining chunks: {pending_chunks:,}")

        print()
        for filepath, count, desc, _ in pending_files:
            filename = filepath.name
            print(f"   - {filename} ({count:,} chunks)")
        print()

    print("=" * 70)
    print()

    # Check if all done
    if not current_file_info and not pending_files:
        print("✅ ALL FILES ALREADY EMBEDDED!")
        print("\nReady for Phase 2:")
        print("  python create_collections.py")
        return

    # Continue or start
    print("💾 Checkpoint system active: Progress saved every 100 chunks")
    print("🛑 You can stop at ANY TIME with Ctrl+C and resume later")
    print()

    full_statistics = []

    # Process current file if in progress
    if current_file_info:
        filepath, filename, expected_count, description, progress, output_path = current_file_info

        print(f"\n\n{'#' * 70}")
        print(f"RESUMING: {filename} (from chunk {progress})")
        print(f"{'#' * 70}")

        try:
            statistics = embed_file_resumable(filepath, output_path, manager, checkpoint, batch_size=100)

            full_statistics.append(statistics)

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print("Progress saved. Run again to resume.")
            raise

    # Process pending files
    for i, (filepath, expected_count, description, output_path) in enumerate(pending_files, 1):
        print(f"\n\n{'#' * 70}")
        print(f"FILE {len(completed_files) + (1 if current_file_info else 0) + i}/{len(in_files_to_embed)}")
        print(f"{'#' * 70}")

        try:
            statistics = embed_file_resumable(filepath, output_path, manager, checkpoint, batch_size=100)

            full_statistics.append(statistics)

            # Show overall progress
            total_completed = len(checkpoint.state["completed_files"])
            print(f"\n📊 Overall: {total_completed}/{len(in_files_to_embed)} files complete")
            print(f"   Total embedded: {checkpoint.state['total_chunks_embedded']:,} chunks")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print("Progress saved. Run again to resume.")
            raise

    # All done!
    print("\n\n" + "=" * 70)
    print("✅ PHASE 1 COMPLETE - ALL FILES EMBEDDED!")
    print("=" * 70)
    print()
    print(f"Total chunks: {checkpoint.state['total_chunks_embedded']:,}")
    print(f"Total time: {checkpoint.state['total_time_seconds'] / 3600:.1f} hours")
    print()
    print("Next: python create_collections.py")
    print()

    total_time = (datetime.now() - start_time).total_seconds()

    print_results_table(full_statistics, "FULL EMBEDDING STATISTICS")
    print_processed_time(total_time)

    reset_log("emb_03_embed_all_chunks")

    log_results(full_statistics, "emb_03_embed_all_chunks", "FULL EMBEDDING STATISTICS")
    log_results_table(full_statistics, "emb_03_embed_all_chunks", "FULL EMBEDDING STATISTICS")
    log_processed_time("emb_03_embed_all_chunks", total_time)


if __name__ == "__main__":
    # Initialize paths from config
    paths = get_paths()

    out_embedding_path = paths.EMBEDDINGS_PATH
    aux_file_embedding_checklpoint = paths.FILE_EMBEDDING_CHECKPOINT

    in_files_to_embed = [
        (paths.FILE_BOOK_CHUNKS, 80000, "Books"),
        (paths.FILE_WIKI_CHUNKS_CHRONOLOGY, 80000, "Wiki Chronology"),
        (paths.FILE_WIKI_CHUNKS_CHARACTER, 80000, "Wiki Character"),
        (paths.FILE_WIKI_CHUNKS_CHAPTER_SUMMARY, 80000, "Wiki Chapter Summary"),
        (paths.FILE_WIKI_CHUNKS_CONCEPT, 80000, "Wiki Concept"),
        (paths.FILE_WIKI_CHUNKS_PROPHECIES, 80000, "Wiki Prophecy"),
        (paths.FILE_WIKI_CHUNKS_MAGIC, 80000, "Wiki Magic"),
    ]

    # Map source files to their partial output paths
    aux_partial_results_paths_map = {
        "book_chunks.jsonl": paths.FILE_BOOK_PARTIAL,
        "wiki_chunks_character.jsonl": paths.FILE_WIKI_CHARACTER_PARTIAL,
        "wiki_chunks_concept.jsonl": paths.FILE_WIKI_CONCEPT_PARTIAL,
        "wiki_chunks_magic.jsonl": paths.FILE_WIKI_MAGIC_PARTIAL,
        "wiki_chunks_prophecies.jsonl": paths.FILE_WIKI_PROPHECIES_PARTIAL,
        "wiki_chunks_chapter_summary.jsonl": paths.FILE_WIKI_CHAPTER_SUMMARY_PARTIAL,
        "wiki_chunks_chronology.jsonl": paths.FILE_WIKI_CHRONOLOGY_PARTIAL,
    }

    try:
        main()
        exit_code = 0
    except Exception as e:
        print(f"\n❌ An error occurred in the script: {str(e)}")
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)
