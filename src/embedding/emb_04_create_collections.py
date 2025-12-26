"""
Dragon's Codex - ChromaDB Collection Builder
Loads pre-generated embeddings and creates ChromaDB collections for retrieval.
"""

import json
import pickle
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import chromadb
from chromadb.config import Settings
from tqdm import tqdm

from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_statistics import total_statistics_logging

# Global path variables (initialized in main)
in_embeddings_path = None
in_file_book_embeddings = None
in_file_wiki_chronology_embeddings = None
in_file_wiki_character_embeddings = None
in_file_wiki_chapter_summary_embeddings = None
in_file_wiki_concept_embeddings = None
in_file_wiki_prophecy_embeddings = None
in_file_wiki_magic_embeddings = None

out_vector_store_path = None
out_collection_books = None
out_collection_narrative = None
out_collection_reference = None


def load_embeddings_from_pickle(filepath: Path) -> Tuple[List[dict], List[List[float]]]:
    """
    Load chunks and embeddings from pickle file.

    Args:
        filepath: Path to .pkl file containing embeddings

    Returns:
        tuple: (chunks, embeddings)
            - chunks: list of chunk dictionaries with metadata
            - embeddings: list of embedding vectors
    """
    print(f"  Loading {filepath.name}...")

    with open(filepath, "rb") as f:
        embeddings_data = pickle.load(f)

    # Format: {chunk_id: {"embedding": [...], "text": "...", "metadata": {...}}}
    if not isinstance(embeddings_data, dict):
        raise ValueError(f"Unexpected pickle format in {filepath.name}")

    # Extract chunks and embeddings
    chunks = []
    embeddings = []

    for chunk_id in sorted(embeddings_data.keys()):  # Sort to maintain order
        data = embeddings_data[chunk_id]

        # Reconstruct chunk with text + metadata
        chunk = {"text": data["text"]}
        chunk.update(data["metadata"])

        chunks.append(chunk)
        embeddings.append(data["embedding"])

    print(f"    ✓ Loaded {len(chunks)} chunks with embeddings")
    return chunks, embeddings


def create_chromadb_collection(client: chromadb.Client, collection_name: str, embedding_files: List[Path], description: str) -> Dict:
    """
    Create or get a ChromaDB collection and populate it with embeddings.

    Args:
        client: ChromaDB client
        collection_name: Name of the collection
        embedding_files: List of pickle files to load
        description: Collection description

    Returns:
        dict: Statistics about the collection
    """
    print(f"\n📦 Creating collection: {collection_name}")
    print(f"   Description: {description}")
    print(f"   Source files: {len(embedding_files)}")

    # Get or create collection
    collection = client.get_or_create_collection(name=collection_name, metadata={"description": description})

    # Track statistics
    total_chunks = 0
    total_added = 0
    files_processed = 0

    chunks_per_file = {}
    # Process each embedding file
    for filepath in embedding_files:
        if not filepath.exists():
            print(f"  ⚠️  File not found: {filepath.name}, skipping...")
            continue

        try:
            # Load embeddings
            chunks, embeddings = load_embeddings_from_pickle(filepath)

            if len(chunks) != len(embeddings):
                print(f"  ⚠️  Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings")
                continue

            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            embedding_vectors = []

            for i, (chunk, embedding) in enumerate(tqdm(zip(chunks, embeddings), desc=f"  Preparing {filepath.stem}", total=len(chunks), unit="chunk")):
                # Generate unique ID
                chunk_id = f"{filepath.stem}_{i}"

                # Extract text (adjust key based on your chunk structure)
                text = chunk.get("text", chunk.get("content", ""))

                # Extract metadata (preserve all metadata fields)
                metadata = {
                    "source": chunk.get("source", "unknown"),
                    "source_type": chunk.get("source_type", "unknown"),
                    "source_file": filepath.stem,
                }

                # Add optional metadata fields if they exist
                optional_fields = [
                    "book_number",
                    "book_title",
                    "chapter_number",
                    "chapter_title",
                    "temporal_order",
                    "character_mentions",
                    "concept_mentions",
                    "magic_mentions",
                    "wiki_page",
                    "section_title",
                ]

                for field in optional_fields:
                    if field in chunk:
                        value = chunk[field]
                        # Skip None values - ChromaDB doesn't accept them
                        if value is None:
                            continue
                        if isinstance(value, list):
                            metadata[field] = json.dumps(value)
                        else:
                            metadata[field] = value

                ids.append(chunk_id)
                documents.append(text)
                metadatas.append(metadata)
                embedding_vectors.append(embedding)

            # Add to collection in batches
            batch_size = 1000
            for i in tqdm(range(0, len(ids), batch_size), desc=f"  Adding to {collection_name}", unit="batch"):
                batch_ids = ids[i : i + batch_size]
                batch_docs = documents[i : i + batch_size]
                batch_meta = metadatas[i : i + batch_size]
                batch_emb = embedding_vectors[i : i + batch_size]

                collection.upsert(ids=batch_ids, documents=batch_docs, metadatas=batch_meta, embeddings=batch_emb)

            total_chunks += len(chunks)
            total_added += len(ids)
            files_processed += 1
            print(f"    ✓ Added {len(ids)} chunks from {filepath.name}")
            chunks_per_file[filepath.name] = len(ids)

        except Exception as e:
            print(f"  ❌ Error processing {filepath.name}: {e}")
            traceback.print_exc()
            continue

    # Get final collection count
    final_count = collection.count()

    statistics = {
        "collection_name": collection_name,
        "files_processed": files_processed,
        "total_chunks_loaded": total_chunks,
        "total_chunks_added": total_added,
        "final_collection_count": final_count,
        "chunks_per_file": chunks_per_file,
    }

    print(f"\n  ✓ Collection '{collection_name}' complete:")
    print(f"    Files processed: {files_processed}")
    print(f"    Total chunks added: {total_added}")
    print(f"    Final count: {final_count}")

    return statistics


def reset_collections(client):
    # Clear existing collections if rebuilding
    print("🗑️  Clearing existing collections...")
    try:
        client.delete_collection(out_collection_books)
        print(f"  ✓ Deleted '{out_collection_books}'")
    except Exception:
        print(f"  • '{out_collection_books}' didn't exist")

    try:
        client.delete_collection(out_collection_narrative)
        print(f"  ✓ Deleted '{out_collection_narrative}'")
    except Exception:
        print(f"  • '{out_collection_narrative}' didn't exist")

    try:
        client.delete_collection(out_collection_reference)
        print(f"  ✓ Deleted '{out_collection_reference}'")
    except Exception:
        print(f"  • '{out_collection_reference}' didn't exist")

    print()


def main():
    """Main execution function"""
    start_time = datetime.now()

    print("=" * 70)
    print("🏗️  CHROMADB COLLECTION BUILDER")
    print("=" * 70)
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Initialize ChromaDB client
    print("📊 Initializing ChromaDB client...")
    client = chromadb.PersistentClient(path=str(out_vector_store_path), settings=Settings(anonymized_telemetry=False, allow_reset=True))
    print(f"  ✓ Client initialized at: {out_vector_store_path}")

    reset_collections(client)

    # Define collection mappings
    collections_config = {
        out_collection_books: {
            "description": "Pure books from 15 main books only (Phase 1 baseline)",
            "files": [
                in_file_book_embeddings,  # Only this one
            ],
        },
        # TODO PHASE 1A
        # out_collection_narrative: {
        #     "description": "Narrative content: story events, chronologies, and chapter summaries",
        #     "files": [
        #         in_file_book_embeddings,
        #         in_file_wiki_chronology_embeddings,
        #         in_file_wiki_chapter_summary_embeddings,
        #     ],
        # },
        # out_collection_reference: {
        #     "description": "Reference content: characters, concepts, magic system, and prophecies",
        #     "files": [
        #         in_file_wiki_character_embeddings,
        #         in_file_wiki_concept_embeddings,
        #         in_file_wiki_magic_embeddings,
        #         in_file_wiki_prophecy_embeddings,
        #     ],
        # },
    }

    # Build collections
    all_statistics = {}
    results = []
    for collection_name, config in collections_config.items():
        # Filter to only existing files
        existing_files = [f for f in config["files"] if f.exists()]

        if not existing_files:
            raise ValueError(f"⚠️  Skipping {collection_name} - no embedding files found")

        stats = create_chromadb_collection(client=client, collection_name=collection_name, embedding_files=existing_files, description=config["description"])

        all_statistics[collection_name] = stats

        metrics = {
            "stats": {
                "files_processed": stats["files_processed"],
                "total_chunks_loaded": stats["total_chunks_loaded"],
                "total_chunks_added": stats["total_chunks_added"],
            },
            "chunks_per_file": stats["chunks_per_file"],
        }

        result = {"name": stats["collection_name"], "metrics": metrics}
        results.append(result)

    # Calculate total time
    total_time = datetime.now() - start_time

    total_statistics_logging(log_name="emb_04_create_collections", statistics=results, tables=False, title="CREATE COLLECTIONS", total_time=total_time)


if __name__ == "__main__":
    # Initialize paths from config
    paths = get_paths()
    config = get_config()

    # Input paths - embedding files
    in_embeddings_path = paths.EMBEDDINGS_PATH
    in_file_book_embeddings = paths.FILE_BOOK_EMBEDDINGS
    in_file_wiki_chronology_embeddings = paths.FILE_WIKI_CHRONOLOGY_EMBEDDINGS
    in_file_wiki_character_embeddings = paths.FILE_WIKI_CHARACTER_EMBEDDINGS
    in_file_wiki_chapter_summary_embeddings = paths.FILE_WIKI_CHAPTER_SUMMARY_EMBEDDINGS
    in_file_wiki_concept_embeddings = paths.FILE_WIKI_CONCEPT_EMBEDDINGS
    in_file_wiki_prophecy_embeddings = paths.FILE_WIKI_PROPHECIES_EMBEDDINGS
    in_file_wiki_magic_embeddings = paths.FILE_WIKI_MAGIC_EMBEDDINGS

    # Output paths - ChromaDB collections
    out_vector_store_path = paths.VECTOR_STORE_PATH
    out_collection_books = config.CHROMA_COLLECTION_BOOKS
    out_collection_narrative = config.CHROMA_COLLECTION_NARRATIVE
    out_collection_reference = config.CHROMA_COLLECTION_REFERENCE

    try:
        main()
        exit_code = 0
    except Exception as e:
        print(f"\n❌ An error occurred in the script: {str(e)}")
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)
