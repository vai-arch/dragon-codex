"""
Dragon's Codex - Configuration Manager
Loads and manages configuration from environment variables.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

from src.utils.paths import get_paths


class Config:
    """
    Configuration manager for Dragon's Codex.
    Loads settings from .env file and provides access to all configuration.
    """

    def __init__(self, env_file=".env"):
        """Initialize configuration by loading .env file"""
        # Load environment variables
        load_dotenv(override=True)

        # Ollama configuration
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # We need a file called Modelifle with this content:
        #
        # FROM nomic-embed-text
        # PARAMETER num_batch 2048
        #
        # and then create a new model based on it:
        # ollama create nomic-embed-text-num_batch-2048 -f Modelfile
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text-num_batch-2048:latest")
        self.LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
        self.NOMIC_EMBED_TEXT_MAX_TOKENS = 2046  # in theory is 2048 but in reallity in real life is 2046

        # Embedding settings
        self.EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", 768))
        self.EMBEDDING_MAX_TOKENS = self.NOMIC_EMBED_TEXT_MAX_TOKENS

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
        self.MAX_TOKENS = int(os.getenv("MAX_TOKENS", self.EMBEDDING_MAX_TOKENS * 0.85))  # Safety limit 15% (0.85) is already tested with all the chunks and the MAX ammount of tekens was 1616
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
        return f"Config(PROJECT_ROOT={self.PROJECT_ROOT}, LLM_MODEL={self.LLM_MODEL}, EMBEDDING_MODEL={self.EMBEDDING_MODEL})"


# Global configuration instance
_config = None


def get_config():
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


# Convenience function for testing
def print_config():
    """Print current configuration (useful for debugging)"""
    config = get_config()

    print("=" * 60)
    print("Dragon's Codex Configuration")
    print("=" * 60)

    print("\n🤖 Models:")
    print(f"  Ollama URL: {config.OLLAMA_BASE_URL}")
    print(f"  LLM: {config.LLM_MODEL}")
    print(f"  Embeddings: {config.EMBEDDING_MODEL}")

    print("\n⚙️  Settings:")
    print(f"  Chunk Size: {config.CHUNK_SIZE}")
    print(f"  Max chunk Size: {config.MAX_CHUNK_SIZE}")
    print(f"  Chunk Overlap: {config.CHUNK_OVERLAP}")
    print(f"  Top-K Retrieval: {config.TOP_K_RETRIEVAL}")
    print(f"  Temperature: {config.LLM_TEMPERATURE}")

    print("\n📊 Collections:")
    print(f"  Narrative: {config.CHROMA_COLLECTION_NARRATIVE}")
    print(f"  Concepts: {config.CHROMA_COLLECTION_CONCEPTS}")
    print(f"  Magic: {config.CHROMA_COLLECTION_MAGIC}")
    print(f"  Prophecies: {config.CHROMA_COLLECTION_PROPHECIES}")

    print("\n📝 Logging:")
    print(f"  Level: {config.LOG_LEVEL}")
    print(f"  Debug: {config.DEBUG}")

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
    # print_config()
    log_configuration("emb_03_embed_all_chunks", "embeddings")
