"""
Dragon's Codex - Baseline Retrieval Evaluation
Score all 100 test questions using the testing rubric.
"""

import json
import sys
from typing import Dict, List

from src.utils.paths import get_paths


# Evaluation rubric
def score_retrieval_quality(question: Dict, chunks: List[Dict]) -> Dict:
    """
    Score retrieval quality for a single question

    Returns:
        dict with:
            - retrieval_score (1-5)
            - relevance_notes
            - issues_found
    """
    q_id = question["question_id"]
    q_text = question["question"]
    expected = question["expected_topics"]
    difficulty = question["difficulty"]
    category = question["category"]

    # Extract chunk texts
    chunk_texts = [c["text"].lower() for c in chunks]
    combined_text = " ".join(chunk_texts)

    score = 0
    issues = []
    positives = []

    # Check if expected topics are covered
    topics_found = 0
    for topic in expected:
        topic_lower = topic.lower()
        # Check for topic or close variants
        if topic_lower in combined_text:
            topics_found += 1
            positives.append(f"Found: {topic}")

    topic_coverage = topics_found / len(expected) if expected else 0

    # Base score on topic coverage
    if topic_coverage >= 0.8:
        score = 5  # Excellent: 80%+ topics covered
    elif topic_coverage >= 0.6:
        score = 4  # Good: 60%+ topics covered
    elif topic_coverage >= 0.4:
        score = 3  # Acceptable: 40%+ topics covered
    elif topic_coverage >= 0.2:
        score = 2  # Poor: 20%+ topics covered
    else:
        score = 1  # Failed: <20% topics covered

    # Adjust for chunk count
    num_chunks = len(chunks)
    if num_chunks == 0:
        score = 1
        issues.append("NO CHUNKS RETRIEVED")
    elif num_chunks < 3:
        issues.append(f"Too few chunks: {num_chunks}")
        score = max(1, score - 1)

    # Check for obviously irrelevant chunks (distance > 1.0 is very poor)
    high_distance_count = sum(1 for c in chunks if c.get("distance", 0) > 1.0)
    if high_distance_count > len(chunks) / 2:
        issues.append(f"Many irrelevant chunks: {high_distance_count}/{len(chunks)}")
        score = max(1, score - 1)

    # Check top chunk relevance (most important)
    if chunks:
        top_chunk = chunks[0]
        top_dist = top_chunk.get("distance", 999)
        top_text = top_chunk["text"].lower()

        # Good distances are typically < 0.7
        if top_dist > 0.9:
            issues.append(f"Top chunk poor match (dist={top_dist:.3f})")
            score = max(1, score - 1)
        elif top_dist < 0.5:
            positives.append(f"Top chunk excellent match (dist={top_dist:.3f})")

        # Check if top chunk is relevant to question
        question_keywords = set(q_text.lower().split())
        relevant_keywords = question_keywords.intersection(set(top_text.split()))
        if len(relevant_keywords) < 2:
            issues.append("Top chunk lacks question keywords")

    # Missing expected topics
    missing_topics = [t for t in expected if t.lower() not in combined_text]
    if missing_topics:
        issues.append(f"Missing topics: {', '.join(missing_topics[:3])}")

    return {
        "retrieval_score": score,
        "topic_coverage": topic_coverage,
        "topics_found": topics_found,
        "topics_expected": len(expected),
        "positives": positives,
        "issues": issues,
        "num_chunks": num_chunks,
        "avg_distance": sum(c.get("distance", 0) for c in chunks) / len(chunks) if chunks else 999,
    }


def evaluate_all_results(data: Dict) -> Dict:
    """Evaluate all 100 questions"""

    results = data["results"]

    # Initialize aggregates
    scores_by_difficulty = {"easy": [], "medium": [], "hard": []}
    scores_by_category = {}

    all_evaluations = []

    print("Evaluating 100 questions...")
    print("=" * 70)

    for result in results:
        q_id = result["question_id"]
        question = {"question_id": q_id, "question": result["question"], "expected_topics": result["expected_topics"], "difficulty": result["difficulty"], "category": result["category"]}

        chunks = result["retrieved_chunks"]

        evaluation = score_retrieval_quality(question, chunks)
        evaluation["question_id"] = q_id
        evaluation["question"] = result["question"]
        evaluation["difficulty"] = result["difficulty"]
        evaluation["category"] = result["category"]
        evaluation["temporal_limit"] = result.get("temporal_limit")

        all_evaluations.append(evaluation)

        # Aggregate by difficulty
        scores_by_difficulty[result["difficulty"]].append(evaluation["retrieval_score"])

        # Aggregate by category
        cat = result["category"]
        if cat not in scores_by_category:
            scores_by_category[cat] = []
        scores_by_category[cat].append(evaluation["retrieval_score"])

    # Calculate statistics
    all_scores = [e["retrieval_score"] for e in all_evaluations]

    statistics = {
        "overall": {
            "average": sum(all_scores) / len(all_scores),
            "median": sorted(all_scores)[len(all_scores) // 2],
            "min": min(all_scores),
            "max": max(all_scores),
            "total_questions": len(all_scores),
        },
        "by_difficulty": {diff: {"average": sum(scores) / len(scores), "count": len(scores)} for diff, scores in scores_by_difficulty.items()},
        "by_category": {cat: {"average": sum(scores) / len(scores), "count": len(scores)} for cat, scores in scores_by_category.items()},
    }

    # Find best and worst
    sorted_evals = sorted(all_evaluations, key=lambda x: x["retrieval_score"])
    worst_5 = sorted_evals[:5]
    best_5 = sorted_evals[-5:]

    return {"evaluations": all_evaluations, "statistics": statistics, "worst_5": worst_5, "best_5": best_5}


def print_summary(analysis: Dict):
    """Print evaluation summary"""
    stats = analysis["statistics"]

    print("\n" + "=" * 70)
    print("BASELINE RETRIEVAL EVALUATION SUMMARY")
    print("=" * 70)

    print("\n📊 OVERALL PERFORMANCE")
    print(f"   Average Score: {stats['overall']['average']:.2f}/5")
    print(f"   Median Score: {stats['overall']['median']}/5")
    print(f"   Range: {stats['overall']['min']}-{stats['overall']['max']}")
    print(f"   Total Questions: {stats['overall']['total_questions']}")

    # MVP threshold check
    mvp_threshold = 3.5
    meets_mvp = stats["overall"]["average"] >= mvp_threshold
    print(f"\n✅ MVP Threshold (≥3.5): {'PASSED' if meets_mvp else 'FAILED'}")

    print("\n📈 BY DIFFICULTY")
    for diff in ["easy", "medium", "hard"]:
        avg = stats["by_difficulty"][diff]["average"]
        count = stats["by_difficulty"][diff]["count"]
        print(f"   {diff.capitalize():8s}: {avg:.2f}/5 ({count} questions)")

    print("\n📂 BY CATEGORY")
    for cat, cat_stats in sorted(stats["by_category"].items()):
        avg = cat_stats["average"]
        count = cat_stats["count"]
        print(f"   {cat:20s}: {avg:.2f}/5 ({count} questions)")

    print("\n🏆 TOP 5 BEST PERFORMING")
    for e in analysis["best_5"]:
        print(f"   Q{e['question_id']:3d} ({e['difficulty']:6s}): {e['retrieval_score']}/5 - {e['question'][:50]}...")

    print("\n⚠️  TOP 5 WORST PERFORMING")
    for e in analysis["worst_5"]:
        print(f"   Q{e['question_id']:3d} ({e['difficulty']:6s}): {e['retrieval_score']}/5 - {e['question'][:50]}...")
        if e["issues"]:
            print(f"       Issues: {'; '.join(e['issues'][:2])}")

    print("\n" + "=" * 70)

    return meets_mvp


def main():
    paths = get_paths()

    results_file = paths.DATA_PATH / "testing" / "answers_baseline_retrieval_semantic_search.json"

    print(f"Loading results from: {results_file}")
    with open(results_file, "r") as f:
        data = json.load(f)

    print(f"Loaded {len(data['results'])} question results")

    # Evaluate
    analysis = evaluate_all_results(data)

    # Print summary
    meets_mvp = print_summary(analysis)

    # Save detailed evaluation
    output_file = paths.DATA_PATH / "testing" / "baseline_evaluation_detailed.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"\n💾 Detailed evaluation saved to: {output_file}")

    # Recommendation
    print("\n📋 RECOMMENDATION")
    if meets_mvp:
        print("   ✅ Baseline performance meets MVP threshold!")
        print("   → System is ready for use")
        print("   → Optional: Try Phase 2 (BM25) for potential improvement")
    else:
        print("   ⚠️  Baseline performance below MVP threshold")
        print("   → Proceed to Phase 2: Hybrid Retrieval (BM25)")
        print("   → Expected improvement: 5-15% on semantic-only baseline")

    return 0 if meets_mvp else 1


if __name__ == "__main__":
    sys.exit(main())
