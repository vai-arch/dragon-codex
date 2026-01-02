"""
Dragon's Codex - Configuration Manager
Loads and manages configuration from environment variables.
"""

import logging
import os
from enum import Enum
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

from src.utils.paths import get_paths


class EmbeddingManagers(str, Enum):
    OLLAMA = "ollama"
    SENTENCE_TRANSFORMER = "sentence_transformer"


class Config:
    """
    Configuration manager for Dragon's Codex.
    Loads settings from .env file and provides access to all configuration.
    """

    def __init__(self, env_file=".env"):
        """Initialize configuration by loading .env file"""
        # Load environment variables
        load_dotenv(override=True)

        # We need a file called Modelifle with this content:
        #
        # FROM nomic-embed-text
        # PARAMETER num_batch 2048
        #
        # and then create a new model based on it:
        # ollama create nomic-embed-text-num_batch-2048 -f Modelfile
        self.EMBEDDING_MODEL_NOMIC_2048 = {
            "EMBEDDING_MODEL_NAME": "nomic-embed-text-num_batch-2048:latest",
            "EMBEDDING_MODEL_MAX_TOKENS": 2046,
            "EMBEDDING_MODEL_DIMENSION": 768,
            "EMBEDDING_MODEL_RAW_PREFIX": None,
            "EMBEDDING_MODEL_SEARCH_PREFIX": "search_query",
            "EMBEDDING_MODEL_DOCUMENT_PREFIX": "search_document",
        }

        self.EMBEDDING_MODEL = self.EMBEDDING_MODEL_NOMIC_2048
        self.EMBEDDING_MANAGER = EmbeddingManagers.OLLAMA.value

        self.LLM_MODEL = {"LLM_MODEL_NAME": "llama3.1:8b"}

        self.OLLAMA_CONFIG = {
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "EMBEDDING_METHOD": "BATCH",  # ONE_BY_ONE, BATCH, BATCH_IN_PARALLEL
            "EMBEDDING_BATCH_SIZE": 32,
            "EMBEDDING_MODEL": self.EMBEDDING_MODEL,
            "LLM_MODEL": self.LLM_MODEL,
        }

        self.CHUNKING_STRATEGY = {
            "BOOKS_CHUNKING_STRATEGY_NAME": "semantic",  # options: "legacy", "semantic", "hybrid". Semantic uses the configured embedding manager/model
            "SEMANTIC_MAX_CHUNK_TOKENS": 1000,
            "SEMANTIC_OVERLAP_TOKENS": 200,
            "SEMANTIC_SIMILARITY_THRESHOLD": 0.82,  # cosine similarity breakpoint
            "MIN_BOOKS_CHUNKS_SIZE_CHARACTERS": 300,
            "WIKI_CHUNKING_STRATEGY_NAME": "hybrid",
            # Characters
            "WIKI_CHARACTER_MIN_SECTION_SIZE": 350,  # ↑ Safer for short bios
            "WIKI_CHARACTER_SEMANTIC_THRESHOLD": 0.78,
            # Chapter Summaries
            "WIKI_CHAPTER_SUMMARY_MIN_SECTION_SIZE": 500,
            "WIKI_CHAPTER_SUMMARY_SEMANTIC_THRESHOLD": 0.78,
            # Chronology
            "WIKI_CHRONOLOGY_MIN_SECTION_SIZE": 400,
            "WIKI_CHRONOLOGY_SEMANTIC_THRESHOLD": 0.85,
            # Concepts/Magic/Prophecies
            "WIKI_CONCEPT_MIN_SECTION_SIZE": 250,  # ↑ Handles stubs better
            "WIKI_CONCEPT_SEMANTIC_THRESHOLD": 0.75,
        }

        self.QUERY_MODEL_TRAINING = {
            "MODEL_NAME": "distilbert-base-uncased",
            "MAX_LENGTH": 128,
            "TEST_SIZE": 0.2,
            "NUM_EPOCHS": 6,
            "TRAIN_BATCH_SIZE": 16,
            "EVAL_BATCH_SIZE": 16,
            "LEARNING_RATE": 5e-5,
            "WEIGHT_DECAY": 0.01,
            "WARMUP_STEPS": 100,
            "SEED": 42,
            "SAVE_TOTAL_LIMIT": 2,
            "LABELS": ["character", "concept", "plot_event", "prophecy", "magic_system", "cross_reference", "relationship", "timeline"],
            ## IN CPU
            # "EVAL_STRATEGY": "no",  # Critical: disables evaluation during training
            # "LOAD_BEST_MODEL_AT_END": False,  # Not needed without evaluation
            # "METRIC_FOR_BEST_MODEL": None,  # Not used
            # "FP16": False,  # False for CPU , True for GPU
            ## IN GPU
            "EVAL_STRATEGY": "epoch",
            "LOAD_BEST_MODEL_AT_END": True,
            "METRIC_FOR_BEST_MODEL": "eval_f1_macro",
            "FP16": True,
        }

        # Final Parameters:

        # Target size: 6000 characters (~1340 tokens)
        # Max size: 7000 characters (~1565 tokens)
        # Min size: 3000 characters (avoid tiny tail chunks)
        # Overlap: 10% (~600 characters, ~1-1.5 paragraphs)
        # Split on: Paragraph boundaries
        # Hard limit: Never exceed 8000 characters (to avoid Ollama's silent truncation at 2046 tokens)

        # This gives us:

        # Safe buffer below the 2046 token limit
        # Good context per chunk for retrieval
        # Reasonable overlap to preserve boundary context
        # Clean paragraph-based splits for narrative coherence

        # Token-based configuration (primary)
        self.CHARS_PER_TOKEN = int(os.getenv("CHARS_PER_TOKEN", 4.5))
        self.MAX_TOKENS = int(
            os.getenv("MAX_TOKENS", self.EMBEDDING_MODEL["EMBEDDING_MODEL_MAX_TOKENS"] * 0.85)
        )  # Safety limit 15% (0.85) is already tested with all the chunks and the MAX ammount of tekens was 1616
        self.TARGET_TOKENS = int(os.getenv("TARGET_TOKENS", self.MAX_TOKENS * 0.86))  # Target = 85%
        self.OVERLAP_TOKENS = int(os.getenv("OVERLAP_TOKENS", self.TARGET_TOKENS * 0.10))  # 10% overlap

        # Character-based (derived from tokens)
        self.CHUNK_SIZE = self.TARGET_TOKENS * self.CHARS_PER_TOKEN
        self.CHUNK_OVERLAP = self.OVERLAP_TOKENS * self.CHARS_PER_TOKEN
        self.MAX_CHUNK_SIZE = self.MAX_TOKENS * self.CHARS_PER_TOKEN

        # LLM settings
        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.7))
        self.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 2000))
        self.LLM_CONTEXT_WINDOW = int(os.getenv("LLM_CONTEXT_WINDOW", 8192))

        # Retrieval settings
        self.TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", 10))
        self.RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", 5))
        self.SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.7))

        # ChromaDB settings
        self.CHROMA_PERSISTENCE = os.getenv("CHROMA_PERSISTENCE", "True").lower() == "true"
        self.CHROMA_COLLECTION_BOOKS = os.getenv("CHROMA_COLLECTION_BOOKS", "books")
        self.CHROMA_COLLECTION_CHARACTERS = os.getenv("CHROMA_COLLECTION_CHARACTERS", "characters")
        self.CHROMA_COLLECTION_NARRATIVE = os.getenv("CHROMA_COLLECTION_NARRATIVE", "narrative")
        self.CHROMA_COLLECTION_REFERENCE = os.getenv("CHROMA_COLLECTION_REFERENCE", "reference")
        # NEW: ChromaDB client settings
        self.CHROMA_TELEMETRY = os.getenv("CHROMA_TELEMETRY", "False").lower() == "true"

        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))  # 10MB
        self.LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))

        # Development
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.VERBOSE = os.getenv("VERBOSE", "True").lower() == "true"

        self.WIKI_BASE_URL = os.getenv("WIKI_BASE_URL", "https://wot.fandom.com")

    def __repr__(self):
        """String representation of configuration"""
        return f"Config(PROJECT_ROOT={self.PROJECT_ROOT})"


# Global configuration instance
_config = None


def get_embedding_manager_config(embedding_manager: str):
    config = get_config()

    if embedding_manager == EmbeddingManagers.OLLAMA.value:
        return config.OLLAMA_CONFIG
    else:
        raise ValueError(f"Unknown embedding backend: {embedding_manager}")


def get_config():
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


# Convenience function for testing
def print_config():
    """Print current configuration (useful for debugging)"""

    print("=" * 60)
    print("Dragon's Codex Configuration")
    print("=" * 60)


def get_configuration_section(configuration_section):
    config = get_config()
    config_items = None

    if configuration_section == "embeddings":
        config_items = [
            ("", ""),
            ("=== Ollama Configuration ===", ""),
            ("Ollama URL", config.OLLAMA_BASE_URL),
            ("Embedding Model", config.EMBEDDING_MODEL),
            ("LLM Model", config.LLM_MODEL),
            ("Nomic Embed Max Tokens", config.NOMIC_EMBED_TEXT_MAX_TOKENS),
            ("\n=== Embedding Settings ===", ""),
            ("Embedding Dimension", config.EMBEDDING_DIMENSION),
            ("Embedding Max Tokens", config.EMBEDDING_MAX_TOKENS),
            ("\n=== Token-Based Chunking Configuration ===", ""),
            ("Chars per Token", config.CHARS_PER_TOKEN),
            ("Max Tokens", config.MAX_TOKENS),
            ("Target Tokens", config.TARGET_TOKENS),
            ("Overlap Tokens", config.OVERLAP_TOKENS),
            ("\n=== Character-Based Chunking (Derived) ===", ""),
            ("Chunk Size (chars)", config.CHUNK_SIZE),
            ("Chunk Overlap (chars)", config.CHUNK_OVERLAP),
            ("Max Chunk Size (chars)", config.MAX_CHUNK_SIZE),
        ]
    return config_items


def print_configuration(configuration_section):
    config_items = get_configuration_section(configuration_section)

    max_label = max(len(label) for label, _ in config_items)
    for label, value in config_items:
        print(f"  {label.ljust(max_label)} : {value}")


def log_configuration(log_file, configuration_section):
    config_items = get_configuration_section(configuration_section)

    logger = get_stats_logger(f"{log_file}.log")

    max_label = max(len(label) for label, _ in config_items)
    for label, value in config_items:
        logger.info(f"  {label.ljust(max_label)} : {value}")


def get_stats_logger(logfile="stats.log"):
    paths = get_paths()
    logger = logging.getLogger("stats_logger")
    logger.setLevel(logging.INFO)

    if not logger.handlers:  # avoid duplicate handlers
        handler = RotatingFileHandler(
            paths.LOG_STATISTICS_PATH / logfile,
            maxBytes=20_000_000,  # 2 MB per file
            backupCount=5,
        )
        formatter = logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


if __name__ == "__main__":
    # Test the configuration
    print_config()
    # log_configuration("emb_03_embed_all_chunks", "embeddings")
