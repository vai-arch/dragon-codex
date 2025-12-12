"""
Dragon's Codex - Configuration Manager
Loads and manages configuration from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    """
    Configuration manager for Dragon's Codex.
    Loads settings from .env file and provides access to all configuration.
    """

    def __init__(self, env_file='.env'):
        """Initialize configuration by loading .env file"""
        # Load environment variables
        load_dotenv(override=True)
        
        # Project paths
        self.PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path.cwd()))
        self.DATA_PATH = self.PROJECT_ROOT / 'data'

        # Raw -> Original unprocessed data files
        self.BOOKS_PATH = self.DATA_PATH / 'raw' / 'books'
        self.WIKI_PATH = self.DATA_PATH / 'raw' / 'wiki'
        self.WIKI_GLOSSARY_PATH = self.DATA_PATH / 'raw' / 'wiki_glossary'
        self.WIKI_ORIGINAL_PATH = self.DATA_PATH / 'raw' / 'wiki_original'
        
        # Processed -> Raw data transformed into structured format (still "data heavy")
        self.PROCESSED_PATH = self.DATA_PATH / 'processed'
        self.PROCESSED_BOOKS_PATH = self.PROCESSED_PATH / 'books'
        self.PROCESSED_WIKI_PATH = self.PROCESSED_PATH / 'wiki'
        # MEtadata -> Derived insights, indexes, and mappings (smaller, reference files)
        self.METADATA_PATH = self.DATA_PATH / 'metadata'
        self.METADATA_BOOKS_PATH = self.METADATA_PATH / 'books'
        self.METADATA_WIKI_PATH = self.METADATA_PATH / 'wiki'

        # Auxiliary paths
        self.AUXILIARY_PATH = self.DATA_PATH / 'auxiliary'
        self.AUXILIARY_BOOKS_PATH = self.AUXILIARY_PATH / 'books'
        self.AUXILIARY_WIKI_PATH = self.AUXILIARY_PATH / 'wiki'

        self.VECTOR_STORE_PATH = self.PROJECT_ROOT / 'vector_stores'
       
        # Auxiliary files
        self.FILE_WIKI_ALL_PAGES = self.AUXILIARY_WIKI_PATH / 'wiki_all_pages.json'
        self.FILE_WIKI_ALL_CATEGORIES = self.AUXILIARY_WIKI_PATH / 'wiki_all_categories.json'
        self.FILE_WIKI_ALL_PAGE_TITLES = self.AUXILIARY_WIKI_PATH / 'wiki_all_page_titles.json'

        # Week 2.5: Metadata Generation
        # ---------------------------------------------------------------------
        # Maps wiki page redirects to their canonical target pages
        self.FILE_REDIRECT_MAPPING = self.METADATA_WIKI_PATH / 'redirect_mapping.json'
        # Maps redirect aliases to their canonical names
        self.FILE_REDIRECT_ALIASES_MAPPING = self.METADATA_WIKI_PATH / 'redirect_aliases_mapping.json'
        # Maps wiki filenames to their category lists for classification
        self.FILE_FILENAME_TO_CATEGORIES = self.METADATA_WIKI_PATH / 'filename_to_categories.json'
        # Maps wiki categories to the list of filenames in each category
        self.FILE_CATEGORY_TO_FILES = self.METADATA_WIKI_PATH / 'category_to_files.json'
        # Unified glossary extracted from all 15 book files (characters, places, terms)
        self.FILE_UNIFIED_GLOSSARY = self.METADATA_BOOKS_PATH / 'unified_glossary.json'
        # Maps glossary term names to their corresponding wiki filenames (100% coverage)
        self.FILE_GLOSSARY_WIKI_MAPPING = self.METADATA_WIKI_PATH / 'glossary_to_wiki_mapping.json'
        # Summary analysis of wiki categories
        self.FILE_CATEGORY_ANALYSIS_SUMMARY = self.AUXILIARY_WIKI_PATH / 'category_analysis_summary.txt'
        
        # Week 3 Goal 2: Parsed Wiki Data
        # ---------------------------------------------------------------------
        # Parsed chronology pages (5 major characters: Rand, Mat, Perrin, Egwene, Elayne)
        self.FILE_WIKI_CHRONOLOGY = self.PROCESSED_WIKI_PATH / 'wiki_chronology.json'
        # Parsed character pages (2,452 characters with biographical/physical/chronological data)
        self.FILE_WIKI_CHARACTER = self.PROCESSED_WIKI_PATH / 'wiki_character.json'
        self.FILE_WIKI_PROPHECIES = self.PROCESSED_WIKI_PATH / 'wiki_prophecies.json'
        self.FILE_WIKI_MAGIC = self.PROCESSED_WIKI_PATH / 'wiki_magic.json'
        # Parsed chapter summary pages (714 chapter summaries across all books)
        self.FILE_WIKI_CHAPTER_SUMMARY = self.PROCESSED_WIKI_PATH / 'wiki_chapter_summary.json'
        # Parsed concept pages (2,716 concepts: places, terms, magic, prophecies, etc.)
        self.FILE_WIKI_CONCEPT = self.PROCESSED_WIKI_PATH / 'wiki_concept.json'
        
        # Week 3 Goal 3: Character Index
        # ---------------------------------------------------------------------
        # Comprehensive character index with aliases, abilities, titles, book appearances
        self.FILE_CHARACTER_INDEX = self.METADATA_WIKI_PATH / 'character_index.json'
        # Index of all prophecies (Karaethon Cycle, Dark Prophecy, viewings, etc.)
        self.FILE_PROPHECY_INDEX = self.METADATA_WIKI_PATH / 'prophecy_index.json'
        # Index of One Power magic system (weaves, objects, terms, strength rankings)
        self.FILE_MAGIC_SYSTEM_INDEX = self.METADATA_WIKI_PATH / 'magic_system_index.json'
        # Index of WoT concepts (locations, creatures, items, historical events, culture)
        self.FILE_CONCEPT_INDEX = self.METADATA_WIKI_PATH / 'concept_index.json'
        
        # Week 2: Book Processing (Pending)
        # ---------------------------------------------------------------------
        # Parsed book structure with chapters, glossaries, and metadata
        self.FILE_BOOKS_STRUCTURED = self.PROCESSED_BOOKS_PATH / 'books_structured.json'
        self.FILE_BOOKS_ALL_PARSED = self.PROCESSED_BOOKS_PATH / 'books_all_parsed.json'
        # Chapter-based chunks from all 15 books with metadata
        
        
        # Week 4: Wiki Chunks (Pending)
        # ---------------------------------------------------------------------
        # Chunked wiki content ready for embedding
        self.CHUNKS_PATH = self.DATA_PATH / 'chunks'
        self.FILE_BOOK_CHUNKS = self.CHUNKS_PATH / 'book_chunks.jsonl'
        self.FILE_WIKI_CHUNKS_CHAPTER_SUMMARY = self.CHUNKS_PATH / 'wiki_chunks_chapter_summary.jsonl'
        self.FILE_WIKI_CHUNKS_CHARACTER = self.CHUNKS_PATH / 'wiki_chunks_character.jsonl'
        self.FILE_WIKI_CHUNKS_CHRONOLOGY = self.CHUNKS_PATH / 'wiki_chunks_chronology.jsonl'
        self.FILE_WIKI_CHUNKS_PROPHECIES = self.CHUNKS_PATH / 'wiki_chunks_prophecies.jsonl'
        self.FILE_WIKI_CHUNKS_MAGIC = self.CHUNKS_PATH / 'wiki_chunks_magic.jsonl'
        self.FILE_WIKI_CHUNKS_CONCEPT = self.CHUNKS_PATH / 'wiki_chunks_concept.jsonl'

        # Week 5: Embedding Storage
        # ---------------------------------------------------------------------
        self.EMBEDDINGS_PATH = self.DATA_PATH / 'embeddings'

        # Checkpoint file for resumable embedding process
        self.FILE_EMBEDDING_CHECKPOINT = self.EMBEDDINGS_PATH / 'checkpoint_v2.json'

        # Embedding files (one per source file)
        self.FILE_BOOK_EMBEDDINGS = self.EMBEDDINGS_PATH / 'book_chunks.embeddings.pkl'
        self.FILE_WIKI_CHARACTER_EMBEDDINGS = self.EMBEDDINGS_PATH / 'wiki_chunks_character.embeddings.pkl'
        self.FILE_WIKI_CONCEPT_EMBEDDINGS = self.EMBEDDINGS_PATH / 'wiki_chunks_concept.embeddings.pkl'
        self.FILE_WIKI_CHAPTER_SUMMARY_EMBEDDINGS = self.EMBEDDINGS_PATH / 'wiki_chunks_chapter_summary.embeddings.pkl'
        self.FILE_WIKI_CHRONOLOGY_EMBEDDINGS = self.EMBEDDINGS_PATH / 'wiki_chunks_chronology.embeddings.pkl'

        # Temporary partial embedding files (used during checkpointing)
        self.FILE_BOOK_PARTIAL = self.EMBEDDINGS_PATH / 'book_chunks.partial.pkl'
        self.FILE_WIKI_CHARACTER_PARTIAL = self.EMBEDDINGS_PATH / 'wiki_chunks_character.partial.pkl'
        self.FILE_WIKI_CONCEPT_PARTIAL = self.EMBEDDINGS_PATH / 'wiki_chunks_concept.partial.pkl'
        self.FILE_WIKI_MAGIC_PARTIAL = self.EMBEDDINGS_PATH / 'wiki_chunks_magic.partial.pkl'
        self.FILE_WIKI_PROPHECIES_PARTIAL = self.EMBEDDINGS_PATH / 'wiki_chunks_prophecies.partial.pkl'
        self.FILE_WIKI_CHAPTER_SUMMARY_PARTIAL = self.EMBEDDINGS_PATH / 'wiki_chunks_chapter_summary.partial.pkl'
        self.FILE_WIKI_CHRONOLOGY_PARTIAL = self.EMBEDDINGS_PATH / 'wiki_chunks_chronology.partial.pkl'
       
        # Ollama configuration
        self.OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        # We need a file called Modelifle with this content:
        # 
        # FROM nomic-embed-text
        # PARAMETER num_batch 2048
        # 
        # and then create a new model based on it: 
        # ollama create nomic-embed-text-num_batch-2048 -f Modelfile
        self.EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text-num_batch-2048:latest')
        self.LLM_MODEL = os.getenv('LLM_MODEL', 'llama3.1:8b')
        
        # Embedding settings
        self.EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', 768))
        # Token-based configuration (primary)
        self.CHARS_PER_TOKEN = int(os.getenv('CHARS_PER_TOKEN', 4))
        self.TARGET_TOKENS = int(os.getenv('TARGET_TOKENS', 1536)) # before was 400
        self.MAX_TOKENS = int(os.getenv('MAX_TOKENS', self.TARGET_TOKENS* 1.25))  # Safety limit 25% more
        self.OVERLAP_TOKENS = int(os.getenv('OVERLAP_TOKENS', self.TARGET_TOKENS*0.20)) # 20% overlap:

        # Character-based (derived from tokens)
        self.CHUNK_SIZE = self.TARGET_TOKENS * self.CHARS_PER_TOKEN      # 1600 chars
        self.CHUNK_OVERLAP = self.OVERLAP_TOKENS * self.CHARS_PER_TOKEN  # 400 chars
        self.MAX_CHUNK_SIZE = self.MAX_TOKENS * self.CHARS_PER_TOKEN     # 2000 chars
        
        # LLM settings
        self.LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', 0.7))
        self.LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', 2000))
        self.LLM_CONTEXT_WINDOW = int(os.getenv('LLM_CONTEXT_WINDOW', 8192))
        
        # Retrieval settings
        self.TOP_K_RETRIEVAL = int(os.getenv('TOP_K_RETRIEVAL', 10))
        self.RERANK_TOP_K = int(os.getenv('RERANK_TOP_K', 5))
        self.SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.7))
        
        # ChromaDB settings
        self.CHROMA_PERSISTENCE = os.getenv('CHROMA_PERSISTENCE', 'True').lower() == 'true'
        self.CHROMA_COLLECTION_NARRATIVE = os.getenv('CHROMA_COLLECTION_NARRATIVE', 'narrative')
        self.CHROMA_COLLECTION_CONCEPTS = os.getenv('CHROMA_COLLECTION_CONCEPTS', 'concepts')
        self.CHROMA_COLLECTION_MAGIC = os.getenv('CHROMA_COLLECTION_MAGIC', 'magic')
        self.CHROMA_COLLECTION_PROPHECIES = os.getenv('CHROMA_COLLECTION_PROPHECIES', 'prophecies')
        # NEW: ChromaDB client settings
        self.CHROMA_TELEMETRY = os.getenv('CHROMA_TELEMETRY', 'False').lower() == 'true'
        
        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        log_file = os.getenv('LOG_FILE', str(self.PROJECT_ROOT / 'logs' / 'dragon_codex.log'))
        self.LOG_FILE = Path(log_file)
        self.LOG_FOLDER = self.LOG_FILE.parent
        self.LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
        
        # Development
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        self.VERBOSE = os.getenv('VERBOSE', 'True').lower() == 'true'
        
        self.WIKI_BASE_URL = os.getenv('WIKI_BASE_URL', 'https://wot.fandom.com') 
        # Ensure necessary directories exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.DATA_PATH,
            self.BOOKS_PATH,
            self.WIKI_PATH,
            self.PROCESSED_PATH,
            self.METADATA_PATH,
            self.VECTOR_STORE_PATH,
            self.LOG_FILE.parent,
            self.EMBEDDINGS_PATH,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def __repr__(self):
        """String representation of configuration"""
        return (f"Config(PROJECT_ROOT={self.PROJECT_ROOT}, "
                f"LLM_MODEL={self.LLM_MODEL}, "
                f"EMBEDDING_MODEL={self.EMBEDDING_MODEL})")


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
    
    print("\n📁 Paths:")
    print(f"  Project Root: {config.PROJECT_ROOT}")
    print(f"  Data Path: {config.DATA_PATH}")
    print(f"  Books: {config.BOOKS_PATH}")
    print(f"  Wiki: {config.WIKI_PATH}")
    print(f"  Vector Stores: {config.VECTOR_STORE_PATH}")
    
    print("\n🤖 Models:")
    print(f"  Ollama URL: {config.OLLAMA_BASE_URL}")
    print(f"  LLM: {config.LLM_MODEL}")
    print(f"  Embeddings: {config.EMBEDDING_MODEL}")
    
    print("\n⚙️  Settings:")
    print(f"  Chunk Size: {config.CHUNK_SIZE}")
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
    print(f"  File: {config.LOG_FILE}")
    print(f"  Debug: {config.DEBUG}")
    
    print("=" * 60)


if __name__ == "__main__":
    # Test the configuration
    print_config()
