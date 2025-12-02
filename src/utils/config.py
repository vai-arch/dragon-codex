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
        self.BOOKS_PATH = self.DATA_PATH / 'raw' / 'books'
        self.WIKI_PATH = self.DATA_PATH / 'raw' / 'wiki'
        self.WIKI_GLOSSARY_PATH = self.DATA_PATH / 'raw' / 'wiki_glossary'
        self.WIKI_ORIGINAL_PATH = self.DATA_PATH / 'raw' / 'wiki_original'
        self.PROCESSED_PATH = self.DATA_PATH / 'processed'
        self.PROCESSED_BOOKS_PATH = self.PROCESSED_PATH / 'books'
        self.PROCESSED_WIKI_PATH = self.PROCESSED_PATH / 'wiki'
        self.METADATA_PATH = self.DATA_PATH / 'metadata'
        self.METADATA_BOOKS_PATH = self.METADATA_PATH / 'books'
        self.METADATA_WIKI_PATH = self.METADATA_PATH / 'wiki'
        self.VECTOR_STORE_PATH = self.PROJECT_ROOT / 'vector_stores'
        
        # Ollama configuration
        self.OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')
        self.LLM_MODEL = os.getenv('LLM_MODEL', 'llama3.1:8b')
        
        # Embedding settings
        self.EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', 768))
        self.CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
        self.CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 100))
        
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
        self.CHROMA_COLLECTION_PROPHECIES = os.getenv('CHROMA_COLLECTION_PROPHECIES', 
                                                      'prophecies')
        
        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        log_file = os.getenv('LOG_FILE', str(self.PROJECT_ROOT / 'logs' / 'dragon_codex.log'))
        self.LOG_FILE = Path(log_file)
        self.LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
        
        # Development
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        self.VERBOSE = os.getenv('VERBOSE', 'True').lower() == 'true'
        
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
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    # def get_book_path(self, book_number):
    #     """Get path to a specific book file"""
    #     # This will be implemented with actual file naming logic
    #     return self.BOOKS_PATH / f"{book_number:02d}-book.md"
    
    # def get_processed_file(self, filename):
    #     """Get path to a processed data file"""
    #     return self.PROCESSED_PATH / filename
    
    # def get_metadata_file(self, filename):
    #     """Get path to a metadata file"""
    #     return self.METADATA_PATH / filename
    
    # def get_vector_store_path(self, collection_name):
    #     """Get path to a vector store collection"""
    #     return self.VECTOR_STORE_PATH / collection_name
    
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
