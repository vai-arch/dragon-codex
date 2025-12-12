"""
Test embeddings

"""

from datetime import datetime
import json
from tqdm import tqdm
from src.utils.util_embedding import VectorStoreManager
from src.utils.util_statistics import print_results, log_results
from src.utils.config import get_config

config = get_config()
manager = VectorStoreManager(config)
BATCH_SIZE = 100

def test_connection():
    # Test connection first
    if not manager.test_connection():
        print("❌ Connection test failed. Fix Ollama before continuing.")
        return False
    
# Test functions for Goal 1
def test_single_embeddings():
    """Test single embedding generation"""

    print("\n=== Testing Single Embedding ===\n")
    
    tokens = 0
    
    # Test single embedding
    text = "Rand al'Thor is the Dragon Reborn"
    print(f"\nEmbedding text: '{text}'")
    
    embedding,tokens = manager.embed_texts([text])
    
    # Validate
    print(f"✅ Embedding generated")
    print(f"   Dimensions: {len(embedding)}")
    print(f"   First 5 values: {embedding[:5]}")
    print(f"   All floats: {all(isinstance(x, float) for x in embedding)}")
    
    # Test consistency
    print("\n=== Testing Consistency ===\n")
    embedding2, tokens = manager.embed_texts([text])
    same = embedding == embedding2
    print(f"Same text → Same embedding: {same}")
    
    # Test different text
    different_text = "Egwene al'Vere becomes Amyrlin Seat"
    embedding3, tokens = manager.embed_texts([different_text])
    different = embedding != embedding3
    print(f"Different text → Different embedding: {different}")
    
    expected_dim = config.EMBEDDING_DIMENSION
    assert len(embedding[0]) == expected_dim, f"Expected {expected_dim} dimensions, got {len(embedding[0])}"
    assert all(isinstance(x, float) for x in embedding[0]), "Not all values are floats"
    assert same, "Same text should produce same embedding"
    assert different, "Different text should produce different embedding"
    
    print("\n✅ Single embedding test PASSED!")
    return True

def util_get_chunks_batch():
    chunks = []
    with open(config.FILE_BOOK_CHUNKS, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= BATCH_SIZE:
                break
            chunks.append(json.loads(line))
    return chunks

def test_batch_one_by_one():
    """Test one by one with Ollama"""
    print("\n=== Test one by one with Ollama ===\n")
    
    chunks = util_get_chunks_batch()

    texts = [chunk['text'] for chunk in chunks] 
    
    embeddings, avg_tokens, max_tokens, total_time =  manager.embed_texts(texts)

    statistics = {
        "name": "One-by-One-Ollama",
        "metrics":{
            "total_time": total_time,
            "avg_time": total_time.total_seconds() / BATCH_SIZE,
            "avg_tokens": avg_tokens,
            "max_tokens": max_tokens
        }
    }

    print_results(statistics)

    return embeddings, statistics

def test_batch_processing():
    """Test batch processing with Ollama"""
    print("\n=== Test batch processing with Ollama ===\n")
    
    chunks = util_get_chunks_batch()

    # Extract texts
    texts = [chunk['text'] for chunk in chunks]
    
    embeddings, avg_tokens, max_tokens, total_time = manager.embed_batch(texts)
    
    statistics = {
        "name": "Batch-Procesing-Ollama",
        "metrics":{
            "total_time": total_time,
            "avg_time": total_time.total_seconds() / BATCH_SIZE,
            "avg_tokens": avg_tokens,
            "max_tokens": -1
        }
    }

    print_results(statistics)

    return embeddings, statistics

def test_parallel_batch_processing():
    """Test parallel batch processing with Ollama"""
    print("\n=== Test parallel batch processing with Ollama ===\n")
    
    chunks = util_get_chunks_batch()

    # Extract texts
    texts = [chunk['text'] for chunk in chunks]
    
    embeddings, avg_tokens, max_tokens, total_time = manager.embed_batch(texts)
    
    statistics = {
        "name": "Batch-Parallel-Procesing-Ollama",
        "metrics":{
            "total_time": total_time,
            "avg_time": total_time.total_seconds() / BATCH_SIZE,
            "avg_tokens": avg_tokens,
            "max_tokens": max_tokens
        }
    }

    print_results(statistics)

    return embeddings, statistics

if __name__ == "__main__":
    """Run all tests in sequence"""
    print("=" * 70)
    print("VECTOR STORE MANAGER - TEST SUITE")
    print("=" * 70)
    
    # # Step 3: Single embedding
    # if not test_single_embedding():
    #     print("\n❌ Single embedding test failed. Fix before continuing.")
    #     exit(1)
    
    results = []    

    BATCH_SIZE = 100

    results.append(test_batch_one_by_one()[1])
    results.append(test_batch_processing()[1])
    results.append(test_parallel_batch_processing()[1])

    print_results(results, f"Testing embedding with {BATCH_SIZE} chunks")
    log_results(results, "embedding_statistics", f"Testing embedding with {BATCH_SIZE} chunks")







