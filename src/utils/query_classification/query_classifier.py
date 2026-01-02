from pathlib import Path
from typing import Dict, List

from transformers import pipeline

from src.utils.config import get_config
from src.utils.paths import get_paths


class QueryClassifier:
    """
    Wrapper for Wheel of Time query classifier.
    - Lazy loads model on first classification
    - Config-driven labels
    - Optional caching
    - Device flexible (CPU/GPU)
    """

    _instance = None  # Singleton pattern optional

    def __init__(self, device: int = -1, use_cache: bool = True):
        self.paths = get_paths()
        self.config = get_config()
        self.model_path = Path(self.paths.QUERY_CLASSIFIER_MODEL_PATH)
        self.labels = self.config.QUERY_MODEL_TRAINING["LABELS"]

        self.device = device  # -1 CPU, 0+ GPU
        self.use_cache = use_cache

        self.classifier = None
        self.cache = {}  # query_text -> result
        self.stats = {
            "queries_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "model_loaded": False,
        }

    def _load_model(self):
        if self.classifier is None:
            if not self.model_path.exists():
                raise FileNotFoundError(f"Classifier model not found at {self.model_path}")

            self.classifier = pipeline(
                "text-classification",
                model=str(self.model_path),
                top_k=None,  # Returns all scores
                device=self.device,
            )
            print(f"Query classifier loaded from {self.model_path} (device: {'GPU' if self.device >= 0 else 'CPU'})")

    def classify(self, query_text: str) -> Dict[str, any]:
        """
        Classify a single query.
        Returns: {"category": str, "confidence": float, "scores": List[Dict]}
        """
        if self.use_cache and query_text in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[query_text]

        self.stats["cache_misses"] += 1

        self._load_model()

        raw_scores = self.classifier(query_text)[0]

        # Convert to dict for easier lookup
        score_map = {item["label"]: item["score"] for item in raw_scores}

        # Predicted category = highest score
        predicted_label = max(score_map, key=score_map.get)
        confidence = score_map[predicted_label]

        if not self.stats["model_loaded"]:
            self.stats["model_loaded"] = True

        result = {
            "category": predicted_label,
            "confidence": confidence,
            "scores": raw_scores,  # Full list for debugging
        }

        if self.use_cache:
            self.cache[query_text] = result

        return result

    def classify_batch(self, queries: List[str]) -> List[Dict[str, any]]:
        """Batch classification for benchmarks."""
        return [self.classify(q) for q in queries]

    def clear_cache(self):
        self.cache.clear()
        self.stats = {
            "queries_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "model_loaded": self.stats["model_loaded"],
        }

    def get_stats(self) -> Dict[str, any]:
        """Return classifier statistics."""
        cache_hit_rate = (self.stats["cache_hits"] / max(self.stats["queries_processed"], 1)) * 100
        return {
            "queries_processed": self.stats["queries_processed"],
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_rate_%": round(cache_hit_rate, 2),
            "model_loaded": self.stats["model_loaded"],
            "cache_size": len(self.cache),
        }


# Optional singleton access
def get_query_classifier(device: int = -1) -> QueryClassifier:
    if QueryClassifier._instance is None:
        QueryClassifier._instance = QueryClassifier(device=device)
    return QueryClassifier._instance
