import shutil

from src.utils.paths import get_paths

paths = get_paths()

# Output paths - Query classifier model collections
out_query_classifier_model_path = paths.QUERY_CLASSIFIER_MODEL_PATH

for sub in out_query_classifier_model_path.iterdir():
    if sub.is_dir() and sub.name.startswith("checkpoint-"):
        shutil.rmtree(sub)
        print(f"🗑️ Removed: {sub}")
