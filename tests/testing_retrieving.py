"""
Dragon's Codex - ChromaDB Diagnostic
Quick script to check what's in ChromaDB collections.
"""

import chromadb

from src.utils.config import get_config
from src.utils.paths import get_paths


def main():
    config = get_config()
    paths = get_paths()

    print("\n" + "=" * 70)
    print("ChromaDB Diagnostic")
    print("=" * 70)

    # Initialize client
    print(f"\n📂 Vector Store Path: {paths.VECTOR_STORE_PATH}")

    try:
        client = chromadb.PersistentClient(path=str(paths.VECTOR_STORE_PATH), settings=chromadb.Settings(anonymized_telemetry=config.CHROMA_TELEMETRY))
        print("✅ ChromaDB client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize ChromaDB client: {e}")
        return 1

    # List all collections
    print("\n📊 All Collections:")
    try:
        all_collections = client.list_collections()
        if not all_collections:
            print("   ⚠️ NO COLLECTIONS FOUND!")
            print("\n   This means embeddings haven't been created yet.")
            print("   Run the embedding script first!")
            return 1

        for coll in all_collections:
            print(f"   - {coll.name}: {coll.count():,} chunks")
    except Exception as e:
        print(f"   ❌ Error listing collections: {e}")
        return 1

    # Check specific collections
    print("\n🔍 Checking Expected Collections:")

    # Narrative
    try:
        narrative = client.get_collection(name=config.CHROMA_COLLECTION_NARRATIVE)
        count = narrative.count()
        print(f"   ✅ {config.CHROMA_COLLECTION_NARRATIVE}: {count:,} chunks")

        if count > 0:
            # Sample one chunk
            sample = narrative.peek(limit=1)
            if sample and sample["ids"]:
                print(f"      Sample ID: {sample['ids'][0]}")
                print(f"      Sample metadata keys: {list(sample['metadatas'][0].keys()) if sample['metadatas'] else 'None'}")

    except Exception as e:
        print(f"   ❌ {config.CHROMA_COLLECTION_NARRATIVE}: {e}")

    # Reference
    try:
        reference = client.get_collection(name=config.CHROMA_COLLECTION_REFERENCE)
        count = reference.count()
        print(f"   ✅ {config.CHROMA_COLLECTION_REFERENCE}: {count:,} chunks")

        if count > 0:
            # Sample one chunk
            sample = reference.peek(limit=1)
            if sample and sample["ids"]:
                print(f"      Sample ID: {sample['ids'][0]}")
                print(f"      Sample metadata keys: {list(sample['metadatas'][0].keys()) if sample['metadatas'] else 'None'}")

    except Exception as e:
        print(f"   ❌ {config.CHROMA_COLLECTION_REFERENCE}: {e}")

    print("\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    exit(main())
