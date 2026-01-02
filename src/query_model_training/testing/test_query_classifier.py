from collections import Counter

import pandas
from transformers import pipeline

from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file
from src.utils.util_statistics import total_statistics_logging

paths = get_paths()
config = get_config()

# Paths - adjust as needed
MODEL_PATH = paths.QUERY_CLASSIFIER_MODEL_PATH  # Your out_query_classifier_model_path
JSON_PATH = paths.FILE_TEST_QUESTIONS  # Or paste content into a file


labels = config.QUERY_MODEL_TRAINING["LABELS"]

# Load model - use top_k=None instead of deprecated return_all_scores
classifier = pipeline(
    "text-classification",
    model=str(MODEL_PATH),
    top_k=None,  # Returns all label scores (multi-label)
    device=-1,  # CPU; change to 0 for GPU
)

data = load_json_from_file(JSON_PATH)
queries = data.get("questions", data)

results = []
exact_matches = 0

print("Processing 100 queries...\n")

for idx, q in enumerate(queries):
    query_text = q["question"]
    ground_truth = [q["category"]]

    # Get all label scores
    preds = classifier(query_text)[0]
    pred_labels = [p["label"] for p in preds if p["score"] > 0.5]

    is_correct = set(ground_truth) == set(pred_labels)
    if is_correct:
        exact_matches += 1

    results.append(
        {
            "id": q.get("question_id", idx + 1),
            "query": query_text,
            "ground_truth": ground_truth,
            "predicted": pred_labels,
            "correct": is_correct,
            "top_prediction": preds[0]["label"] if preds else "none",
            "top_score": preds[0]["score"] if preds else 0.0,
        }
    )

# Final results
accuracy = exact_matches / len(queries)
print(f"\nExact Match Accuracy: {accuracy:.4f} ({exact_matches}/{len(queries)})")

# Save CSV
df = pandas.DataFrame(results)  # This will now work
df.to_csv("query_classifier_final_test_results.csv", index=False)
print("Results saved to query_classifier_final_test_results.csv")


MAX_MISMATCHES_LOGGED = 10

mismatches = [r for r in results if not r["correct"]]

mismatch_summary = {
    "count": len(mismatches),
    "examples": [
        {
            "id": m["id"],
            "ground_truth": m["ground_truth"],
            "predicted": m["predicted"],
            "top_prediction": m["top_prediction"],
            "top_score": round(float(m["top_score"]), 4),
        }
        for m in mismatches[:MAX_MISMATCHES_LOGGED]
    ],
}

mismatch_summary["top_confusions"] = Counter((tuple(m["ground_truth"]), tuple(m["predicted"])) for m in mismatches).most_common(5)

if exact_matches == len(queries):
    print("\n🎉 PERFECT CLASSIFIER: 100/100 correct!")
else:
    print(f"\nMismatches ({mismatch_summary['count']}):")
    for m in mismatch_summary["examples"]:
        print(f"ID {m['id']}: GT {m['ground_truth']} | Pred {m['predicted']} | Top: {m['top_prediction']} ({m['top_score']:.4f})")


statistics = {
    "name": "test_query_classifier",
    "metrics": {
        "match_accuracy": f"{accuracy:.4f}",
        "exact_matches": exact_matches,
        "total_queries": len(queries),
        "mismatches": mismatch_summary,
    },
}

total_statistics_logging(
    log_name="test_query_classifier",
    statistics=statistics,
    tables=False,
    title="TESTING QUERY CLASSIFIER TRAINING",
    total_time=0,
)
