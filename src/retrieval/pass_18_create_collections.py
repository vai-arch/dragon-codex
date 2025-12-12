"""
Create ChromaDB Collections - Phase 2 of Collection Creation

This script creates three ChromaDB collections from pre-computed embeddings.
Expected runtime: <30 minutes (fast, just loading and storing)

Collections:
1. "narrative" - 7,374 book chunks
2. "concepts" - 17,399 wiki chunks
3. "magic" - ~2,992 filtered chunks with magic mentions

Uses config.py for all paths and settings.

Usage:
    python create_collections.py                    # Create all collections
    python create_collections.py --collection narrative  # Create specific collection
    python create_collections.py --reset            # Delete and recreate all
"""

import json
import pickle
import os
import sys
import time
from pathlib import Path
from typing import Dict, List
from src.retrieval.pass_16_uses_this_vector_store import VectorStoreManager
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.utils.config import Config, get_config

manager = VectorStoreManager(get_config())
   
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("❌ ChromaDB not installed!")
    print("\nInstall with:")
    print("  pip install chromadb --break-system-packages")
    sys.exit(1)


def load_embeddings(embedding_path: Path) -> Dict:
    """Load embeddings from pickle file"""
    print(f"Loading embeddings from {embedding_path.name}...")
    
    if not embedding_path.exists():
        raise FileNotFoundError(f"Embedding file not found: {embedding_path}")
    
    with open(embedding_path, 'rb') as f:
        data = pickle.load(f)
    
    file_size_mb = embedding_path.stat().st_size / (1024 * 1024)
    print(f"✅ Loaded {len(data)} chunks ({file_size_mb:.1f} MB)")
    
    return data


def convert_metadata_for_chromadb(metadata: dict) -> dict:
    """Convert metadata to ChromaDB-compatible format"""
    converted = {}
    for key, value in metadata.items():
        if isinstance(value, list):
            # Convert lists to comma-separated strings
            converted[key] = ','.join(str(v) for v in value)
        elif value is None:
            # Convert None to string 'null'
            converted[key] = 'null'
        else:
            # Keep as-is (strings, numbers, bools)
            converted[key] = str(value)
    return converted


def create_narrative_collection(client: chromadb.Client, config, reset: bool = False):
    """Create narrative collection from book chunks"""
    print("\n" + "="*70)
    print("CREATING NARRATIVE COLLECTION")
    print("="*70)
    print()
    
    collection_name = config.CHROMA_COLLECTION_NARRATIVE
    
    # Delete if exists
    if reset:
        try:
            client.delete_collection(collection_name)
            print(f"Deleted existing '{collection_name}' collection")
        except:
            pass
    
    # Load embeddings
    embeddings_data = load_embeddings(config.FILE_BOOK_EMBEDDINGS)
    
    # Create collection
    print(f"\nCreating collection: {collection_name}")
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Book narrative chunks with character evolution"}
    )
    
    # Prepare data for ChromaDB
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for chunk_id, data in embeddings_data.items():
        ids.append(f"narrative_{chunk_id}")
        embeddings.append(data['embedding'])
        documents.append(data['text'])
        metadatas.append(convert_metadata_for_chromadb(data['metadata']))
    
    # Add to collection in batches
    batch_size = 1000
    total = len(ids)
    
    print(f"\nAdding {total:,} documents to collection...")
    for i in range(0, total, batch_size):
        end_idx = min(i + batch_size, total)
        
        collection.add(
            ids=ids[i:end_idx],
            embeddings=embeddings[i:end_idx],
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx]
        )
        
        print(f"  Added batch {i//batch_size + 1}: {end_idx}/{total} documents")
    
    # Verify
    count = collection.count()
    print(f"\n✅ Collection '{collection_name}' created!")
    print(f"   Documents: {count:,}")
    
    # Test query
    print(f"\nTesting query...")
    results = manager.query("Rand al'Thor Dragon Reborn", collection_name, k=3)
    
    print(f"✅ Test query returned {len(results)} results")
    if results:
        print(f"   Sample result: {results[0]['text'][:100]}...")
    
    return collection


def create_concepts_collection(client: chromadb.Client, config, reset: bool = False):
    """Create concepts collection from all wiki chunks"""
    print("\n" + "="*70)
    print("CREATING CONCEPTS COLLECTION")
    print("="*70)
    print()
    
    collection_name = config.CHROMA_COLLECTION_CONCEPTS
    
    # Delete if exists
    if reset:
        try:
            client.delete_collection(collection_name)
            print(f"Deleted existing '{collection_name}' collection")
        except:
            pass
    
    # Load all wiki embeddings using config paths
    wiki_files = [
        config.FILE_WIKI_CHARACTER_EMBEDDINGS,
        config.FILE_WIKI_CONCEPT_EMBEDDINGS,
        config.FILE_WIKI_CHRONOLOGY_EMBEDDINGS,
        config.FILE_WIKI_CHAPTER_SUMMARY_EMBEDDINGS,
    ]
    
    all_embeddings = {}
    for filepath in wiki_files:
        data = load_embeddings(filepath)
        # Prefix IDs to avoid collisions
        prefix = filepath.stem.replace('.embeddings', '')
        for chunk_id, chunk_data in data.items():
            all_embeddings[f"{prefix}_{chunk_id}"] = chunk_data
    
    print(f"\nTotal wiki chunks: {len(all_embeddings):,}")
    
    # Create collection
    print(f"\nCreating collection: {collection_name}")
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Wiki chunks for WoT lore and definitions"}
    )
    
    # Prepare data
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for chunk_id, data in all_embeddings.items():
        ids.append(f"concepts_{chunk_id}")
        embeddings.append(data['embedding'])
        documents.append(data['text'])
        metadatas.append(convert_metadata_for_chromadb(data['metadata']))
    
    # Add to collection in batches
    batch_size = 1000
    total = len(ids)
    
    print(f"\nAdding {total:,} documents to collection...")
    for i in range(0, total, batch_size):
        end_idx = min(i + batch_size, total)
        
        collection.add(
            ids=ids[i:end_idx],
            embeddings=embeddings[i:end_idx],
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx]
        )
        
        print(f"  Added batch {i//batch_size + 1}: {end_idx}/{total} documents")
    
    # Verify
    count = collection.count()
    print(f"\n✅ Collection '{collection_name}' created!")
    print(f"   Documents: {count:,}")
    
    # Test query
    print(f"\nTesting query...")
    results = manager.query("One Power channeling saidin saidar", collection_name, k=3)
    
    print(f"✅ Test query returned {len(results)} results")
    if results:
        print(f"   Sample result: {results[0]['text'][:100]}...")
    
    return collection


def create_magic_collection(client: chromadb.Client, config, reset: bool = False):
    """Create magic collection from chunks with magic_mentions"""
    print("\n" + "="*70)
    print("CREATING MAGIC COLLECTION")
    print("="*70)
    print()
    
    collection_name = config.CHROMA_COLLECTION_MAGIC
    
    # Delete if exists
    if reset:
        try:
            client.delete_collection(collection_name)
            print(f"Deleted existing '{collection_name}' collection")
        except:
            pass
    
    # Load all embedding files using config paths
    all_files = [
        config.FILE_BOOK_EMBEDDINGS,
        config.FILE_WIKI_CHARACTER_EMBEDDINGS,
        config.FILE_WIKI_CONCEPT_EMBEDDINGS,
        config.FILE_WIKI_CHAPTER_SUMMARY_EMBEDDINGS,
        config.FILE_WIKI_CHRONOLOGY_EMBEDDINGS
    ]
    
    # Filter chunks with magic_mentions
    magic_chunks = {}
    
    for filepath in all_files:
        data = load_embeddings(filepath)
        prefix = filepath.stem.replace('.embeddings', '')
        
        for chunk_id, chunk_data in data.items():
            # Check if has magic_mentions
            magic_mentions = chunk_data['metadata'].get('magic_mentions', [])
            
            # Handle string representation of list (if any)
            if isinstance(magic_mentions, str):
                magic_mentions = eval(magic_mentions) if magic_mentions != "null" else []
            
            if magic_mentions and len(magic_mentions) > 0:
                magic_chunks[f"{prefix}_{chunk_id}"] = chunk_data
    
    print(f"\nFiltered magic chunks: {len(magic_chunks):,}")
    
    # Create collection
    print(f"\nCreating collection: {collection_name}")
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Chunks with magic system mentions"}
    )
    
    # Prepare data
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for chunk_id, data in magic_chunks.items():
        ids.append(f"magic_{chunk_id}")
        embeddings.append(data['embedding'])
        documents.append(data['text'])
        metadatas.append(convert_metadata_for_chromadb(data['metadata']))
    
    # Add to collection in batches
    batch_size = 1000
    total = len(ids)
    
    print(f"\nAdding {total:,} documents to collection...")
    for i in range(0, total, batch_size):
        end_idx = min(i + batch_size, total)
        
        collection.add(
            ids=ids[i:end_idx],
            embeddings=embeddings[i:end_idx],
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx]
        )
        
        print(f"  Added batch {i//batch_size + 1}: {end_idx}/{total} documents")
    
    # Verify
    count = collection.count()
    print(f"\n✅ Collection '{collection_name}' created!")
    print(f"   Documents: {count:,}")
    
    # Test query
    print(f"\nTesting query...")
    results = manager.query("balefire weave saidin", collection_name, k=3)
    
    print(f"✅ Test query returned {len(results)} results")
    if results:
        print(f"   Sample result: {results[0]['text'][:100]}...")
    
    return collection


def verify_all_collections(client: chromadb.Client, config):
    """Verify all collections exist and have correct counts"""
    print("\n" + "="*70)
    print("VERIFYING ALL COLLECTIONS")
    print("="*70)
    print()
    
    expected = {
        config.CHROMA_COLLECTION_NARRATIVE: 7374,
        config.CHROMA_COLLECTION_CONCEPTS: 17399,  # 10745 + 5872 + 756 + 26
        config.CHROMA_COLLECTION_MAGIC: None  # Variable, should be ~2992
    }
    
    collections = client.list_collections()
    collection_names = [c.name for c in collections]
    
    print(f"Collections found: {len(collection_names)}")
    print()
    
    for name, expected_count in expected.items():
        if name in collection_names:
            collection = client.get_collection(name)
            actual_count = collection.count()
            
            status = "✅"
            if expected_count and actual_count != expected_count:
                status = "⚠️ "
            
            print(f"{status} {name:12} {actual_count:6,} documents", end="")
            if expected_count:
                print(f" (expected: {expected_count:,})")
            else:
                print()
        else:
            print(f"❌ {name:12} NOT FOUND")
    
    print()


def test_persistence(client: chromadb.Client, config):
    """Test that collections persist across sessions"""
    print("\n" + "="*70)
    print("TESTING PERSISTENCE")
    print("="*70)
    print()
    
    print("Creating new client to simulate restart...")
    
    new_client = chromadb.PersistentClient(path=str(config.VECTOR_STORE_PATH), settings=Settings(anonymized_telemetry=config.CHROMA_TELEMETRY))
    
    collections = new_client.list_collections()
    print(f"✅ Collections still exist: {[c.name for c in collections]}")
    
    # Test query on narrative
    collection = new_client.get_collection(config.CHROMA_COLLECTION_NARRATIVE)
    count = collection.count()
    print(f"✅ Narrative collection accessible: {count:,} documents")
    
    print("\n✅ Persistence test PASSED!")


def main(collection: str = None, reset: bool = False):
    """Main collection creation process"""
    print("="*70)
    print("CREATE CHROMADB COLLECTIONS - PHASE 2")
    print("="*70)
    print()
    
    # Initialize config
    config = get_config()
    
    # Check embeddings exist
    required_files = [
        config.FILE_BOOK_EMBEDDINGS,
        config.FILE_WIKI_CHRONOLOGY_EMBEDDINGS,
        config.FILE_WIKI_CHAPTER_SUMMARY_EMBEDDINGS,
        config.FILE_WIKI_CONCEPT_EMBEDDINGS,
        config.FILE_WIKI_CHARACTER_EMBEDDINGS,
    ]
    
    missing = [f for f in required_files if not f.exists()]
    if missing:
        print("❌ Missing embedding files:")
        for f in missing:
            print(f"   - {f}")
        print("\nRun Phase 1 first: python embed_all_chunks_v2.py")
        return
    
    print("✅ All embedding files found")
    print()
    
    # Initialize ChromaDB using config path
    print("Initializing ChromaDB...")
    persist_directory = config.VECTOR_STORE_PATH
    persist_directory.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(path=str(persist_directory), settings=Settings(anonymized_telemetry=config.CHROMA_TELEMETRY))
    print(f"✅ ChromaDB initialized at {persist_directory}")
    
    # Create collections
    start_time = time.time()
    
    if collection is None or collection == config.CHROMA_COLLECTION_NARRATIVE:
        create_narrative_collection(client, config, reset)
    
    if collection is None or collection == config.CHROMA_COLLECTION_CONCEPTS:
        create_concepts_collection(client, config, reset)
    
    if collection is None or collection == config.CHROMA_COLLECTION_MAGIC:
        create_magic_collection(client, config, reset)
    
    elapsed = time.time() - start_time
    
    # Verify
    if collection is None:
        verify_all_collections(client, config)
        test_persistence(client, config)
    
    # Summary
    print("\n" + "="*70)
    print("✅ PHASE 2 COMPLETE - ALL COLLECTIONS CREATED!")
    print("="*70)
    print()
    print(f"Time taken: {elapsed/60:.1f} minutes")
    print()
    print("Collections:")
    print(f"  - {config.CHROMA_COLLECTION_NARRATIVE}: Book chunks for character/plot queries")
    print(f"  - {config.CHROMA_COLLECTION_CONCEPTS}: Wiki chunks for lore/definition queries")
    print(f"  - {config.CHROMA_COLLECTION_MAGIC}: Magic system chunks for Power queries")
    print()
    print("Next: Test queries (Goal 3)")
    print("  python test_queries.py")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create ChromaDB collections")
    parser.add_argument('--collection', choices=['narrative', 'concepts', 'magic'], 
                       help='Create specific collection only')
    parser.add_argument('--reset', action='store_true', 
                       help='Delete and recreate collections')
    args = parser.parse_args()
    
    reset = args.reset

    reset = True  # Always reset concepts collection due to changes
   
    try:
        main(collection=args.collection, reset=reset)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise