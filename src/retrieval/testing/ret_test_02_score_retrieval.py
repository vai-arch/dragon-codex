import argparse
import json
import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.paths import get_paths
from src.utils.util_files_functions import save_json_to_file

_phase = "1A1"


def load_data(questions_file, phase_file):
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)["questions"]
    with open(phase_file, "r", encoding="utf-8") as f:
        results = json.load(f)["results"]
    return questions, results


def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9\s'\-]", "", text.lower())  # Keep ' and -


def keyword_overlap(expected, chunks_text):
    expected_tokens = set(re.findall(r"\b[\w'-]+\b", " ".join(expected).lower()))
    chunk_tokens = set(re.findall(r"\b[\w'-]+\b", " ".join(chunks_text).lower()))
    if not expected_tokens:
        return 1.0
    return len(expected_tokens & chunk_tokens) / len(expected_tokens)


def semantic_match(expected, chunks_text):
    if not expected or not chunks_text:
        return 1.0 if not expected else 0.0
    vectorizer = TfidfVectorizer()
    all_texts = [" ".join(expected)] + chunks_text
    tfidf_matrix = vectorizer.fit_transform([clean_text(t) for t in all_texts])
    sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).mean()
    return sim


def source_match(sample_citation, chunks):
    if not sample_citation:
        return 5.0
    expected_sources = [clean_text(s.strip()) for s in sample_citation.split(";")]
    chunk_sources = [clean_text(c.get("source", "") + " " + c.get("source_file", "") + " " + str(c.get("book_number", ""))) for c in chunks]
    matches = sum(any(es in cs for cs in chunk_sources) for es in expected_sources)
    return (matches / len(expected_sources)) * 5


def spoiler_check(temporal_limit, chunks):
    if temporal_limit is None:
        return "Pass"
    chunk_books = []
    for c in chunks:
        book_num = c.get("temporal_order") or c.get("book_number")
        if book_num:
            try:
                chunk_books.append(int(book_num))
            except (ValueError, TypeError):
                pass
    return "Pass" if all(b <= temporal_limit for b in chunk_books) else "Fail"


def get_diagnostics(q, res):
    expected = q.get("expected_topics", [])
    chunks = res.get("retrieved_chunks", [])[:5]  # top 5 only for logging
    chunks_text = [c["text"] for c in chunks]

    # Coverage: which expected topics appear in any chunk?
    expected_clean = [clean_text(t) for t in expected]
    covered = []
    for exp in expected_clean:
        if any(exp in clean_text(chunk) for chunk in chunks_text):
            covered.append(exp)

    # Precision: % of retrieved chunks that contain at least one expected topic
    relevant_chunks = sum(any(clean_text(exp) in clean_text(chunk) for exp in expected) for chunk in chunks_text)
    precision = relevant_chunks / len(chunks_text) if chunks_text else 0.0

    return {
        "coverage_ratio": len(covered) / len(expected) if expected else 1.0,
        "covered_topics": covered,
        "precision": precision,
        "top_chunks_snippets": [c["text"][:200] + "..." for c in chunks],
        "chunk_sources": [f"{c.get('source_file', '?')} - {c.get('source', '?')}" for c in chunks],
    }


def score_question(q, res):
    expected_topics = q.get("expected_topics", [])
    chunks = res.get("retrieved_chunks", [])
    chunks_text = [c["text"] for c in chunks]

    # <<< IMPROVEMENT 3: Sub-scores
    coverage = keyword_overlap(expected_topics, chunks_text)
    precision = sum(any(clean_text(exp) in clean_text(chunk) for exp in expected_topics) for chunk in chunks_text)
    precision = precision / len(chunks_text) if chunks_text else 0.0
    semantic_sim = semantic_match(expected_topics, chunks_text)

    # Combine into single retrieval_quality (average of coverage, precision, semantic)
    retrieval_quality = (coverage + precision + semantic_sim) / 3 * 5

    # <<< IMPROVEMENT 2: Better citation scoring
    source_citations = source_match(q.get("sample_citation", ""), chunks)

    # <<< IMPROVEMENT 5: Separate spoiler
    spoiler_prevention = spoiler_check(q.get("temporal_limit"), chunks)

    # <<< IMPROVEMENT 4: Diagnostics
    diagnostics = get_diagnostics(q, res)

    # <<< IMPROVEMENT 1: Smarter flagging
    flag = retrieval_quality < 2.5 or source_citations < 2.0 or spoiler_prevention == "Fail" or diagnostics["coverage_ratio"] < 0.3

    return {
        "question_id": q["question_id"],
        "retrieval_quality": round(retrieval_quality, 2),
        "retrieval_coverage": round(coverage * 5, 2),
        "retrieval_precision": round(precision * 5, 2),
        "retrieval_semantic": round(semantic_sim * 5, 2),
        "source_citations": round(source_citations, 2),
        "spoiler_prevention": spoiler_prevention,
        "flag_manual_review": flag,
        "diagnostics": diagnostics,
    }


def aggregate_scores(scores, questions):
    df = pd.DataFrame(scores)
    df["category"] = [q["category"] for q in questions]
    df["difficulty"] = [q["difficulty"] for q in questions]

    # Overall diagnostics averages
    diag_df = pd.json_normalize(df["diagnostics"])
    diag_avg = diag_df.mean(numeric_only=True).to_dict()

    agg = {
        "Overall": df[["retrieval_quality", "source_citations", "flag_manual_review"]].mean(numeric_only=True).to_dict(),
        "By Category": df.groupby("category")[["retrieval_quality", "source_citations", "flag_manual_review"]].mean(numeric_only=True).to_dict("index"),
        "By Difficulty": df.groupby("difficulty")[["retrieval_quality", "source_citations", "flag_manual_review"]].mean(numeric_only=True).to_dict("index"),
        "Spoiler Pass %": round((df["spoiler_prevention"] == "Pass").mean() * 100, 1),
        "Flagged Questions": df[df["flag_manual_review"]]["question_id"].tolist(),
        "Diagnostics": {
            "avg_coverage_ratio": round(diag_avg.get("coverage_ratio", 0), 3),
            "avg_precision": round(diag_avg.get("precision", 0), 3),
        },
    }

    # Add question_id averages for context
    agg["Overall"]["question_id"] = df["question_id"].mean()
    for group in ["By Category", "By Difficulty"]:
        for key in agg[group]:
            agg[group][key]["question_id"] = df[df["category" if group == "By Category" else "difficulty"] == key]["question_id"].mean()

    return agg


def compare_phases(prev_scores, curr_scores):
    df_prev = pd.DataFrame(prev_scores)
    df_curr = pd.DataFrame(curr_scores)
    deltas = (df_curr.mean(numeric_only=True) - df_prev.mean(numeric_only=True)).to_dict()
    return {k: round(v, 3) for k, v in deltas.items() if k != "question_id"}


if __name__ == "__main__":
    paths = get_paths()
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions_file", default=None)
    parser.add_argument("--phase_file", default=None)
    parser.add_argument("--output_file", default=None)
    parser.add_argument("--compare_phase", default=None)
    args = parser.parse_args()

    in_questions_file = args.questions_file or paths.FILE_TEST_QUESTIONS
    in_answers_file = args.phase_file or (paths.RETRIEVAL_TESTING_RESULTS_PATH / f"answers_{_phase}_retrieval.json")
    out_scores = args.output_file or (paths.RETRIEVAL_TESTING_RESULTS_PATH / f"out_scores_{_phase}.json")

    questions, results = load_data(in_questions_file, in_answers_file)

    scores = [score_question(q, next(r for r in results if r["question_id"] == q["question_id"])) for q in questions]

    agg = aggregate_scores(scores, questions)

    output = {"scores": scores, "aggregates": agg}

    if args.compare_phase:
        prev_questions, prev_results = load_data(in_questions_file, args.compare_phase)
        prev_scores = [score_question(q, next(r for r in prev_results if r["question_id"] == q["question_id"])) for q in prev_questions]
        output["deltas"] = compare_phases(prev_scores, scores)

    def convert_to_native(obj):
        if isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(i) for i in obj]
        elif hasattr(obj, "item"):  # numpy/pandas scalars
            return obj.item()
        elif isinstance(obj, (pd.Series, pd.DataFrame)):
            return convert_to_native(obj.to_dict())
        else:
            return obj

    safe_output = convert_to_native(output)
    save_json_to_file(data=safe_output, output_file=out_scores, indent=2)

    print("\nAggregates:\n", json.dumps(agg, indent=2))
