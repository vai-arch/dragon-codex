import sys
import traceback
from datetime import datetime

import bm25s

from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_line_by_line, save_json_to_file
from src.utils.util_statistics import total_statistics_logging

in_file_book_chunks = None
out_file_bm25_mapping = None
out_bm25_index_path = None


def main():
    start_time = datetime.now()

    chunks = load_json_line_by_line(in_file_book_chunks)

    print("First chunk preview:")
    print("  chunk_id:", chunks[0]["chunk_id"])
    print("  book_title:", chunks[0]["book_title"])
    print("  text preview:", chunks[0]["text"][:150] + "..." if len(chunks[0]["text"]) > 150 else chunks[0]["text"])

    # Extract
    texts = [chunk["text"] for chunk in chunks]
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    metadata_list = [{k: v for k, v in chunk.items() if k != "text"} for chunk in chunks]

    # Tokenize with default (WoT apostrophes preserved well)
    print("Tokenizing corpus...")
    corpus_tokens = bm25s.tokenize(texts, stemmer=None)

    # Create retriever with corpus texts (required for save/load)
    print("Building BM25 retriever...")
    retriever = bm25s.BM25(corpus=texts)
    retriever.index(corpus_tokens)

    # Save the BM25 index (includes vocab, scores, etc.)
    print(f"Saving BM25 index to {out_bm25_index_path}...")
    retriever.save(out_bm25_index_path)

    # Save our custom mapping (chunk_ids + rich metadata)
    mapping = {"chunk_ids": chunk_ids, "metadata": metadata_list}

    save_json_to_file(mapping, out_file_bm25_mapping, indent=2)

    statistics = {
        "name": "bm25_index",
        "metrics": {
            "num_chunks_indexed": len(chunks),
        },
    }

    total_time = datetime.now() - start_time
    total_statistics_logging(total_time=total_time, log_name="prc_10_build_bm25_index", statistics=statistics, title="BM25 Index", tables=False)


if __name__ == "__main__":
    paths = get_paths()

    in_file_book_chunks = paths.FILE_BOOK_CHUNKS
    out_file_bm25_mapping = paths.FILE_BM25_MAPPING
    out_bm25_index_path = paths.BM25_INDEX_PATH

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
