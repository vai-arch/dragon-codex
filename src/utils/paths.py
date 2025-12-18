"""
Dragon's Codex - Configuration Manager
Loads and manages configuration from environment variables.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


class Paths:
    """
    Configuration manager for Dragon's Codex.
    Loads settings from .env file and provides access to all configuration.
    """

    def __init__(self, env_file=".env"):
        """Initialize configuration by loading .env file"""
        # Load environment variables
        load_dotenv(override=True)

        # Project paths
        self.PROJECT_ROOT_PATH = Path(os.getenv("PROJECT_ROOT", Path.cwd()))
        self.DATA_PATH = self.PROJECT_ROOT_PATH / "data"

        # Raw -> Original unprocessed data files
        self.BOOKS_PATH = self.DATA_PATH / "raw" / "books"
        self.WIKI_PATH = self.DATA_PATH / "raw" / "wiki"
        self.WIKI_GLOSSARY_PATH = self.DATA_PATH / "raw" / "wiki_glossary"
        self.WIKI_ORIGINAL_PATH = self.DATA_PATH / "raw" / "wiki_original"

        # Processed -> Raw data transformed into structured format (still "data heavy")
        self.PROCESSED_PATH = self.DATA_PATH / "processed"
        self.PROCESSED_BOOKS_PATH = self.PROCESSED_PATH / "books"
        self.PROCESSED_WIKI_PATH = self.PROCESSED_PATH / "wiki"

        # MEtadata -> Derived insights, indexes, and mappings (smaller, reference files)
        self.METADATA_PATH = self.DATA_PATH / "metadata"
        self.METADATA_BOOKS_PATH = self.METADATA_PATH / "books"
        self.METADATA_WIKI_PATH = self.METADATA_PATH / "wiki"

        # Auxiliary paths
        self.AUXILIARY_PATH = self.DATA_PATH / "auxiliary"
        self.AUXILIARY_BOOKS_PATH = self.AUXILIARY_PATH / "books"
        self.AUXILIARY_WIKI_PATH = self.AUXILIARY_PATH / "wiki"

        # Chunks and embeddings
        self.CHUNKS_PATH = self.DATA_PATH / "chunks"
        self.VECTOR_STORE_PATH = self.PROJECT_ROOT_PATH / "vector_stores"
        self.EMBEDDINGS_PATH = self.DATA_PATH / "embeddings"

        # Retrieval
        self.RETRIEVAL_TESTING_PATH = self.DATA_PATH / "testing"
        self.RETRIEVAL_TESTING_RESULTS_PATH = self.RETRIEVAL_TESTING_PATH / "results"

        # Auxiliary files
        self.FILE_WIKI_ALL_PAGES = self.AUXILIARY_WIKI_PATH / "wiki_all_pages.json"
        self.FILE_WIKI_ALL_CATEGORIES = self.AUXILIARY_WIKI_PATH / "wiki_all_categories.json"
        self.FILE_WIKI_ALL_PAGE_TITLES = self.AUXILIARY_WIKI_PATH / "wiki_all_page_titles.json"

        # Logs
        self.LOG_PATH = self.PROJECT_ROOT_PATH / "logs"
        self.LOG_STATISTICS_PATH = Path(os.environ.get("STATISTICS_PATH", self.LOG_PATH / "statistics"))

        self.FILE_LOG = self.LOG_PATH / "dragon_codex.log"

        # Week 2.5: Metadata Generation
        # ---------------------------------------------------------------------
        # Maps wiki page redirects to their canonical target pages
        self.FILE_REDIRECT_MAPPING = self.METADATA_WIKI_PATH / "redirect_mapping.json"
        # Maps redirect aliases to their canonical names
        self.FILE_REDIRECT_ALIASES_MAPPING = self.METADATA_WIKI_PATH / "redirect_aliases_mapping.json"
        # Maps wiki filenames to their category lists for classification
        self.FILE_FILENAME_TO_CATEGORIES = self.METADATA_WIKI_PATH / "filename_to_categories.json"
        # Maps wiki categories to the list of filenames in each category
        self.FILE_CATEGORY_TO_FILES = self.METADATA_WIKI_PATH / "category_to_files.json"
        # Unified glossary extracted from all 15 book files (characters, places, terms)
        self.FILE_UNIFIED_GLOSSARY = self.METADATA_BOOKS_PATH / "unified_glossary.json"
        self.FILE_ALL_CHAPTERS = self.METADATA_BOOKS_PATH / "all_chapters.json"
        # Maps glossary term names to their corresponding wiki filenames (100% coverage)
        self.FILE_GLOSSARY_WIKI_MAPPING = self.METADATA_WIKI_PATH / "glossary_to_wiki_mapping.json"
        # Summary analysis of wiki categories
        self.FILE_CATEGORY_ANALYSIS_SUMMARY = self.AUXILIARY_WIKI_PATH / "category_analysis_summary.txt"

        # Week 3 Goal 2: Parsed Wiki Data
        # ---------------------------------------------------------------------
        # Parsed chronology pages (5 major characters: Rand, Mat, Perrin, Egwene, Elayne)
        self.FILE_WIKI_CHRONOLOGY = self.PROCESSED_WIKI_PATH / "wiki_chronology.json"
        # Parsed character pages (2,452 characters with biographical/physical/chronological data)
        self.FILE_WIKI_CHARACTER = self.PROCESSED_WIKI_PATH / "wiki_character.json"
        self.FILE_WIKI_PROPHECIES = self.PROCESSED_WIKI_PATH / "wiki_prophecies.json"
        self.FILE_WIKI_MAGIC = self.PROCESSED_WIKI_PATH / "wiki_magic.json"
        # Parsed chapter summary pages (714 chapter summaries across all books)
        self.FILE_WIKI_CHAPTER_SUMMARY = self.PROCESSED_WIKI_PATH / "wiki_chapter_summary.json"
        # Parsed concept pages (2,716 concepts: places, terms, magic, prophecies, etc.)
        self.FILE_WIKI_CONCEPT = self.PROCESSED_WIKI_PATH / "wiki_concept.json"

        # Week 3 Goal 3: Character Index
        # ---------------------------------------------------------------------
        # Comprehensive character index with aliases, abilities, titles, book appearances
        self.FILE_CHARACTER_INDEX = self.METADATA_WIKI_PATH / "character_index.json"
        # Index of all prophecies (Karaethon Cycle, Dark Prophecy, viewings, etc.)
        self.FILE_PROPHECY_INDEX = self.METADATA_WIKI_PATH / "prophecy_index.json"
        # Index of One Power magic system (weaves, objects, terms, strength rankings)
        self.FILE_MAGIC_SYSTEM_INDEX = self.METADATA_WIKI_PATH / "magic_system_index.json"
        # Index of WoT concepts (locations, creatures, items, historical events, culture)
        self.FILE_CONCEPT_INDEX = self.METADATA_WIKI_PATH / "concept_index.json"

        # Week 2: Book Processing (Pending)
        # ---------------------------------------------------------------------
        # Parsed book structure with chapters, glossaries, and metadata
        self.FILE_BOOKS_ALL_PARSED = self.PROCESSED_BOOKS_PATH / "books_all_parsed.json"

        # Week 4: Wiki Chunks (Pending)
        # ---------------------------------------------------------------------
        # Chunked wiki content ready for embedding
        self.FILE_BOOK_CHUNKS = self.CHUNKS_PATH / "book_chunks.jsonl"
        self.FILE_WIKI_CHUNKS_CHAPTER_SUMMARY = self.CHUNKS_PATH / "wiki_chunks_chapter_summary.jsonl"
        self.FILE_WIKI_CHUNKS_CHARACTER = self.CHUNKS_PATH / "wiki_chunks_character.jsonl"
        self.FILE_WIKI_CHUNKS_CHRONOLOGY = self.CHUNKS_PATH / "wiki_chunks_chronology.jsonl"
        self.FILE_WIKI_CHUNKS_PROPHECIES = self.CHUNKS_PATH / "wiki_chunks_prophecies.jsonl"
        self.FILE_WIKI_CHUNKS_MAGIC = self.CHUNKS_PATH / "wiki_chunks_magic.jsonl"
        self.FILE_WIKI_CHUNKS_CONCEPT = self.CHUNKS_PATH / "wiki_chunks_concept.jsonl"

        # Week 5: Embedding Storage
        # ---------------------------------------------------------------------
        # Checkpoint file for resumable embedding process
        self.FILE_EMBEDDING_CHECKPOINT = self.EMBEDDINGS_PATH / "checkpoint_v2.json"
        # Embedding files (one per source file)
        self.FILE_BOOK_EMBEDDINGS = self.EMBEDDINGS_PATH / "book_chunks.embeddings.pkl"
        self.FILE_WIKI_CHARACTER_EMBEDDINGS = self.EMBEDDINGS_PATH / "wiki_chunks_character.embeddings.pkl"
        self.FILE_WIKI_CONCEPT_EMBEDDINGS = self.EMBEDDINGS_PATH / "wiki_chunks_concept.embeddings.pkl"
        self.FILE_WIKI_CHAPTER_SUMMARY_EMBEDDINGS = self.EMBEDDINGS_PATH / "wiki_chunks_chapter_summary.embeddings.pkl"
        self.FILE_WIKI_CHRONOLOGY_EMBEDDINGS = self.EMBEDDINGS_PATH / "wiki_chunks_chronology.embeddings.pkl"
        self.FILE_WIKI_PROPHECIES_EMBEDDINGS = self.EMBEDDINGS_PATH / "wiki_chunks_prophecies.embeddings.pkl"
        self.FILE_WIKI_MAGIC_EMBEDDINGS = self.EMBEDDINGS_PATH / "wiki_chunks_magic.embeddings.pkl"

        # Temporary partial embedding files (used during checkpointing)
        self.FILE_BOOK_PARTIAL = self.EMBEDDINGS_PATH / "book_chunks.partial.pkl"
        self.FILE_WIKI_CHARACTER_PARTIAL = self.EMBEDDINGS_PATH / "wiki_chunks_character.partial.pkl"
        self.FILE_WIKI_CONCEPT_PARTIAL = self.EMBEDDINGS_PATH / "wiki_chunks_concept.partial.pkl"
        self.FILE_WIKI_MAGIC_PARTIAL = self.EMBEDDINGS_PATH / "wiki_chunks_magic.partial.pkl"
        self.FILE_WIKI_PROPHECIES_PARTIAL = self.EMBEDDINGS_PATH / "wiki_chunks_prophecies.partial.pkl"
        self.FILE_WIKI_CHAPTER_SUMMARY_PARTIAL = self.EMBEDDINGS_PATH / "wiki_chunks_chapter_summary.partial.pkl"
        self.FILE_WIKI_CHRONOLOGY_PARTIAL = self.EMBEDDINGS_PATH / "wiki_chunks_chronology.partial.pkl"

        self.FILE_TEST_QUESTIONS = self.DATA_PATH / "testing" / "questions_100.json"
        self._create_directories()

    def _create_directories(self):
        """Create necessary directories if they don't exist"""

        for name, value in self.__dict__.items():
            if name.endswith("_PATH") and isinstance(value, Path):
                value.mkdir(parents=True, exist_ok=True)

    def __repr__(self):
        """String representation of configuration"""
        return f"Config(PROJECT_ROOT={self.PROJECT_ROOT_PATH}, LLM_MODEL={self.LLM_MODEL}, EMBEDDING_MODEL={self.EMBEDDING_MODEL})"


# Global configuration instance
_paths = None


def get_paths():
    """Get the global configuration instance"""
    global _paths
    if _paths is None:
        _paths = Paths()
    return _paths


# Convenience function for testing
def print_paths():
    """Print current configuration (useful for debugging)"""
    paths = get_paths()

    print("=" * 60)
    print("Dragon's Codex Paths & Files")
    print("=" * 60)

    print("\n📁 PATHS:")

    for name, value in paths.__dict__.items():
        if name.endswith("_PATH") and isinstance(value, Path):
            print(f"{name}: {value}")

    print("\n📁 FILES:")

    for name, value in paths.__dict__.items():
        if name.startswith("FILE_") and isinstance(value, Path):
            print(f"{name}: {value}")


if __name__ == "__main__":
    # Test the configuration
    print_paths()
