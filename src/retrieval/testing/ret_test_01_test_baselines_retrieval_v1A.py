"""
Dragon's Codex - Enhanced Retrieval Test Script
Phase 1: Isolated testing of retrieval quality

Improvements:
- Full compatibility with questions_100_improved.json
- Phase tagging (1A, 1B, 1C)
- Richer statistics by category/difficulty
- Proxy recall metric using sample_citation
- Better diagnostics and logging
- Per-question timing

Output: data/testing/answers_{phase}_retrieval.json
"""

import sys
import traceback
from datetime import datetime, timedelta
from typing import List

from tqdm import tqdm

from src.retrieval.query_engine_just_semantics import QueryEngine
from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file, save_json_to_file
from src.utils.util_statistics import total_statistics_logging

_phase = "1A1"


def parse_sample_citation(citation: str) -> list[dict]:
    """Parse sample_citation into list of expected sources with book/chapter"""
    if not citation:
        return []
    expectations = []
    for part in citation.split(";"):
        part = part.strip()
        if "Wiki:" in part or "Glossary" in part:
            continue  # Ignore wiki for Phase 1
        # Handle "Book Title, Ch. X"
        if "," in part:
            book_part, ch_part = [p.strip() for p in part.split(",", 1)]
            ch_num = None
            if ch_part.startswith("Ch."):
                try:
                    ch_num = int(ch_part.split()[1])
                except (ValueError, IndexError):
                    pass
            expectations.append({"book_title": book_part.replace(" ", "_"), "chapter_number": ch_num})
        else:
            # Just book title
            expectations.append({"book_title": part.replace(" ", "_")})
    return expectations


def estimate_recall_proxy(retrieved_chunks: list, expected_sources: list) -> float:
    if not expected_sources or not retrieved_chunks:
        return 0.0 if expected_sources else 1.0

    matched_chunks = 0
    for chunk in retrieved_chunks:
        meta = chunk.get("metadata", {})
        book_title = meta.get("book_title", "")
        chapter_num = meta.get("chapter_number")

        for exp in expected_sources:
            title_match = exp.get("book_title") and exp["book_title"] in book_title
            chapter_match = exp.get("chapter_number") is None or exp["chapter_number"] == chapter_num
            if title_match and chapter_match:
                matched_chunks += 1
                break  # One match per chunk sufficient

    return matched_chunks / len(retrieved_chunks)


def process_single_question(question_data: dict, query_engine: QueryEngine) -> dict:
    question_id = question_data["question_id"]
    question_text = question_data["question"]
    temporal_limit = question_data.get("temporal_limit")
    category = question_data["category"]
    difficulty = question_data["difficulty"]

    start_time = datetime.now()
    result = query_engine.execute_query(
        query_text=question_text,
        temporal_limit=temporal_limit,
        force_category=None,
    )
    query_time = (datetime.now() - start_time).total_seconds()

    retrieved_chunks = []
    source_files = set()
    for chunk in result["results"]["chunks"]:
        meta = chunk["metadata"]
        chunk_info = {
            "text": chunk["text"],
            "distance": chunk["distance"],
            "source": meta.get("source", "unknown"),
            "source_file": meta.get("source_file", "unknown"),
            "temporal_order": meta.get("temporal_order"),
            "book_number": meta.get("book_number"),  # assuming you add this
        }
        retrieved_chunks.append(chunk_info)
        source_files.add(meta.get("source_file", "unknown"))

    # Proxy recall using sample_citation
    expected_sources = parse_sample_citation(question_data.get("sample_citation", ""))
    recall_proxy = estimate_recall_proxy(retrieved_chunks, expected_sources)

    return {
        "question_id": question_id,
        "question": question_text,
        "category": category,
        "difficulty": difficulty,
        "temporal_limit": temporal_limit,
        "expected_topics": question_data.get("expected_topics", []),
        "key_challenges": question_data.get("key_challenges", []),
        "sample_citation": question_data.get("sample_citation", ""),
        "expected_sources": list(expected_sources),
        # Retrieval results
        "detected_category": result["category"],
        "classification_confidence": result["confidence"],
        "routing_strategy": result["routing"]["routing_strategy"],
        "collections_used": result["routing"]["collections_used"],
        "total_chunks_retrieved": result["metadata"]["total_chunks_retrieved"],
        "retrieved_chunks": retrieved_chunks,
        "unique_sources_retrieved": list(source_files),
        "query_time_seconds": round(query_time, 3),
        "recall_proxy": round(recall_proxy, 3),
        "warning_zero_chunks": len(retrieved_chunks) == 0,
        "warning_low_confidence": result["confidence"] < 0.7 if result["confidence"] else False,
    }


def run_retrieval_tests(test_questions: List[dict], query_engine: QueryEngine, phase: str) -> tuple:
    results = []
    stats = {
        "by_category": {},
        "by_difficulty": {},
        "warnings": {"zero_chunks": [], "low_confidence": []},
        "source_distribution": {},
    }

    total_chunks = 0
    total_time = timedelta()

    print(f"\n🔍 Running Phase {phase} retrieval tests on {len(test_questions)} questions...\n")

    for q in tqdm(test_questions, desc="Retrieving"):
        res = process_single_question(q, query_engine)
        results.append(res)

        cat = res["category"]
        diff = res["difficulty"]
        stats["by_category"].setdefault(cat, {"count": 0, "chunks": 0, "time": 0.0, "recall": 0.0})
        stats["by_difficulty"].setdefault(diff, {"count": 0, "chunks": 0, "time": 0.0, "recall": 0.0})

        stats["by_category"][cat]["count"] += 1
        stats["by_category"][cat]["chunks"] += res["total_chunks_retrieved"]
        stats["by_category"][cat]["time"] += res["query_time_seconds"]
        stats["by_category"][cat]["recall"] += res["recall_proxy"]

        stats["by_difficulty"][diff]["count"] += 1
        stats["by_difficulty"][diff]["chunks"] += res["total_chunks_retrieved"]
        stats["by_difficulty"][diff]["time"] += res["query_time_seconds"]
        stats["by_difficulty"][diff]["recall"] += res["recall_proxy"]

        total_chunks += res["total_chunks_retrieved"]
        total_time += timedelta(seconds=res["query_time_seconds"])

        # Collect warnings
        if res["warning_zero_chunks"]:
            stats["warnings"]["zero_chunks"].append(res["question_id"])
        if res["warning_low_confidence"]:
            stats["warnings"]["low_confidence"].append(res["question_id"])

        # Source distribution
        for src in res["unique_sources_retrieved"]:
            stats["source_distribution"][src] = stats["source_distribution"].get(src, 0) + 1

    # Final averages
    for cat_data in stats["by_category"].values():
        cat_data["avg_chunks"] = cat_data["chunks"] / cat_data["count"]
        cat_data["avg_time"] = cat_data["time"] / cat_data["count"]
        cat_data["avg_recall_proxy"] = cat_data["recall"] / cat_data["count"]

    for diff_data in stats["by_difficulty"].values():
        diff_data["avg_chunks"] = diff_data["chunks"] / diff_data["count"]
        diff_data["avg_time"] = diff_data["time"] / diff_data["count"]
        diff_data["avg_recall_proxy"] = diff_data["recall"] / diff_data["count"]

    overall_stats = {
        "phase": phase,
        "total_questions": len(test_questions),
        "total_chunks_retrieved": total_chunks,
        "avg_chunks_per_query": round(total_chunks / len(test_questions), 2),
        "total_time_seconds": total_time.total_seconds(),
        "avg_time_per_query": round(total_time.total_seconds() / len(test_questions), 3),
        "warnings": stats["warnings"],
        "top_sources": sorted(stats["source_distribution"].items(), key=lambda x: x[1], reverse=True)[:10],
    }

    return results, {**overall_stats, "by_category": stats["by_category"], "by_difficulty": stats["by_difficulty"]}


def main():
    global query_engine

    start_time = datetime.now()
    paths = get_paths()
    config = get_config()

    in_test_questions_file = paths.FILE_TEST_QUESTIONS  # points to questions_100_improved.json
    out_dir = paths.RETRIEVAL_TESTING_RESULTS_PATH
    out_dir.mkdir(parents=True, exist_ok=True)
    out_results_file = out_dir / f"answers_{_phase}_retrieval.json"

    if not in_test_questions_file.exists():
        print(f"❌ Test questions file not found: {in_test_questions_file}")
        sys.exit(1)

    print(f"🚀 Starting Phase {_phase}: Pure Semantic Retrieval Test\n")
    print(f"📂 Loading questions from: {in_test_questions_file.name}")

    test_data = load_json_from_file(in_test_questions_file)
    test_questions = test_data["questions"]
    print(f"✅ Loaded {len(test_questions)} improved questions\n")

    print("🔧 Initializing Query Engine (books only)...")
    query_engine = QueryEngine(config)

    stats = query_engine.get_stats()
    print("\n📊 Active Collections:")
    for name, s in stats["collections"].items():
        print(f"   {name}: {s['count']:,} chunks")

    results, statistics = run_retrieval_tests(test_questions, query_engine, _phase)

    output_data = {
        "metadata": {
            "phase": _phase,
            "test_date": datetime.now().isoformat(),
            "questions_file": in_test_questions_file.name,
            "total_questions": len(test_questions),
        },
        "results": results,
        "statistics": statistics,
    }

    save_json_to_file(output_data, out_results_file, indent=2)

    total_time = datetime.now() - start_time

    results = {"name": "phase-1A", "metrics": statistics}
    total_statistics_logging(
        statistics=results,
        total_time=total_time,
        title=f"PHASE {_phase} - RETRIEVAL TEST",
        log_name=f"ret_test_phase_{_phase}",
        tables=False,
    )

    # Summary highlights
    print(f"\n🎯 Phase {_phase} Summary:")
    print(f"   Avg chunks/query: {statistics['avg_chunks_per_query']}")
    print(f"   Avg time/query:   {statistics['avg_time_per_query']}s")
    print(f"   Zero chunks:      {len(statistics['warnings']['zero_chunks'])} questions")
    print(f"   Low confidence:   {len(statistics['warnings']['low_confidence'])} questions")

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=str, default="1A1", help="Test phase: 1A, 1B, 1C")
    args = parser.parse_args()

    try:
        exit_code = main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)
