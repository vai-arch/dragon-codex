"""Test configuration module"""
from src.utils.config import Config

def test_config():
    print("="*70)
    print("Testing Config Module")
    print("="*70)
    
    config = Config()
    
    # Test basic attributes
    print(f"\n✓ Project Root: {config.PROJECT_ROOT}")
    print(f"✓ Data Path: {config.DATA_PATH}")
    print(f"✓ Books Path: {config.BOOKS_PATH}")
    print(f"✓ Wiki Path: {config.WIKI_PATH}")
    
    # Test methods
    book_path = config.get_book_path(1)
    print(f"\n✓ get_book_path(1): {book_path}")
    
    processed_file = config.get_processed_file('test.json')
    print(f"✓ get_processed_file('test.json'): {processed_file}")
    
    metadata_file = config.get_metadata_file('test_meta.json')
    print(f"✓ get_metadata_file('test_meta.json'): {metadata_file}")
    
    vector_store = config.get_vector_store_path('test_store')
    print(f"✓ get_vector_store_path('test_store'): {vector_store}")
    
    print("\n" + "="*70)
    print("✓✓✓ Config module works correctly!")
    print("="*70)

if __name__ == "__main__":
    test_config()