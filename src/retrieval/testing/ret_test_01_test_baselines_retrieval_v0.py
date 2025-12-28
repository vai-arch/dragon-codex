"""
Dragon's Codex - Baseline Retrieval Test
Phase 1: Test pure retrieval quality (no LLM generation yet)

This script:
1. Loads 100 test questions from test_questions_100.json
2. For each question, retrieves top chunks using QueryEngine
3. Saves results for manual evaluation
4. Generates retrieval statistics

Output: data/testing/baseline_retrieval_results.json
"""

import sys
import traceback
from datetime import datetime

from tqdm import tqdm

from src.retrieval.query_engine import QueryEngine
from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file, save_json_to_file
from src.utils.util_statistics import total_statistics_logging

# Global variables
in_test_questions_file = None
out_results_file = None
query_engine = None


def process_single_question(question_data: dict) -> dict:
    """
    Process a single test question

    Args:
        question_data: Question dict from test_questions_100.json

    Returns:
        dict with question + retrieval results
    """
    question_id = question_data["question_id"]
    question_text = question_data["question"]
    temporal_limit = question_data.get("temporal_limit")
    category = question_data["category"]
    difficulty = question_data["difficulty"]

    # Execute query
    result = query_engine.execute_query(
        query_text=question_text,
        temporal_limit=temporal_limit,
        force_category=None,  # Let it auto-classify for now
    )

    # Extract relevant info for evaluation
    retrieved_chunks = []
    for chunk in result["results"]["chunks"]:
        retrieved_chunks.append(
            {
                "text": chunk["text"],
                "distance": chunk["distance"],
                "source": chunk["metadata"].get("source", "unknown"),
                "source_file": chunk["metadata"].get("source_file", "unknown"),
                "temporal_order": chunk["metadata"].get("temporal_order"),
            }
        )

    return {
        "question_id": question_id,
        "question": question_text,
        "category": category,
        "difficulty": difficulty,
        "temporal_limit": temporal_limit,
        "expected_topics": question_data.get("expected_topics", []),
        # Retrieval results
        "detected_category": result["category"],
        "classification_confidence": result["confidence"],
        "routing_strategy": result["routing"]["routing_strategy"],
        "collections_used": result["routing"]["collections_used"],
        "total_chunks_retrieved": result["metadata"]["total_chunks_retrieved"],
        "retrieved_chunks": retrieved_chunks,
        # Metadata for analysis
        "temporal_filter_applied": temporal_limit is not None,
    }


def run_retrieval_tests(test_questions: list) -> tuple:
    """
    Run retrieval tests on all questions

    Args:
        test_questions: List of question dicts

    Returns:
        tuple: (results_list, statistics_dict)
    """
    results = []

    # Statistics tracking
    total_chunks_retrieved = 0
    category_counts = {}
    difficulty_counts = {}
    temporal_filter_count = 0

    print(f"\n🔍 Running retrieval tests on {len(test_questions)} questions...")

    for question_data in tqdm(test_questions, desc="Processing questions"):
        result = process_single_question(question_data)
        results.append(result)

        # Update statistics
        total_chunks_retrieved += result["total_chunks_retrieved"]

        category = result["category"]
        category_counts[category] = category_counts.get(category, 0) + 1

        difficulty = result["difficulty"]
        difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

        if result["temporal_filter_applied"]:
            temporal_filter_count += 1

    # Calculate averages
    avg_chunks_per_query = total_chunks_retrieved / len(test_questions)

    statistics = {
        "name": "baseline_retrieval",
        "metrics": {
            "total_questions": len(test_questions),
            "total_chunks_retrieved": total_chunks_retrieved,
            "avg_chunks_per_query": avg_chunks_per_query,
            "temporal_filter_count": temporal_filter_count,
            "category_distribution": category_counts,
            "difficulty_distribution": difficulty_counts,
        },
    }

    return results, statistics


def main():
    """Main execution function"""
    global query_engine

    start_time = datetime.now()

    # Load test questions
    test_data = load_json_from_file(in_test_questions_file)
    test_questions = test_data["questions"]
    print(f"✅ Loaded {len(test_questions)} test questions")

    # Initialize query engine
    print("\n🔧 Initializing Query Engine...")
    config = get_config()
    query_engine = QueryEngine(config)

    # Show collection stats
    stats = query_engine.get_stats()
    print("\n📊 Collection Statistics:")
    for coll_name, coll_stats in stats["collections"].items():
        print(f"   {coll_name}: {coll_stats['count']:,} chunks")

    # Run retrieval tests
    results, statistics = run_retrieval_tests(test_questions)

    # Save results
    output_data = {
        "metadata": {
            "test_date": datetime.now().isoformat(),
            "phase": "baseline",
            "total_questions": len(test_questions),
            "collections_used": list(stats["collections"].keys()),
        },
        "results": results,
        "statistics": statistics["metrics"],
    }

    save_json_to_file(output_data, out_results_file, indent=2)

    # Print summary
    total_time = datetime.now() - start_time

    total_statistics_logging(statistics=statistics, total_time=total_time, title="BASELINE RETRIEVAL TEST", log_name="ret_test_01_test_baselines_retrievalº", tables=False)

    return 0


if __name__ == "__main__":
    # Initialize paths
    paths = get_paths()
    config = get_config()

    # Set file paths
    in_test_questions_file = paths.FILE_TEST_QUESTIONS
    out_results_file = paths.RETRIEVAL_TESTING_RESULTS_PATH / "answers_baseline_retrieval_semantic_search.json"

    try:
        exit_code = main()
    except Exception as e:
        print(f"❌ An error occurred in the script: {str(e)}")
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)
