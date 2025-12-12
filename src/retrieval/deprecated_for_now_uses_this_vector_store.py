"""
Vector Store Manager for Dragon's Codex

Handles:
- Embedding generation via Ollama
- Batch processing with progress tracking
- ChromaDB collection management
- Query functionality with temporal filtering

Week 5 - Goals 1-3
Uses config.py for all settings and paths
"""

import sys
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Tuple
from tqdm import tqdm
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("❌ ChromaDB not installed!")
    print("\nInstall with:")
    print("  pip install chromadb --break-system-packages")
    sys.exit(1)

from pathlib import Path


class VectorStoreManager:
    """Manages embeddings and vector storage for Dragon's Codex"""
    
    def __init__(self, config=None):
        """
        Initialize Vector Store Manager
        
        Args:
            config: Config object (if None, loads from get_config())
        """
        if config is None:
            from src.utils.config import get_config
            config = get_config()
        
        self.config = config
        self.ollama_url = config.OLLAMA_BASE_URL
        self.model = config.EMBEDDING_MODEL
        self._client = None  # Lazy-loaded ChromaDB client
        self.session = requests.Session()  # Reuse TCP connections
        
    @property
    def client(self):
        """Lazy-load ChromaDB client"""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=str(self.config.VECTOR_STORE_PATH),
                settings=Settings(anonymized_telemetry=self.config.CHROMA_TELEMETRY)
            )
        return self._client
        
    def test_connection(self) -> bool:
        """
        Test if Ollama is running and model is available
        
        Returns:
            bool: True if connection successful
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": "test"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                embedding = response.json().get('embedding', [])
                expected_dim = self.config.EMBEDDING_DIMENSION
                print(f"✅ Ollama connected. Model: {self.model}")
                print(f"   Embedding dim: {len(embedding)} (expected: {expected_dim})")
                return True
            else:
                print(f"❌ Ollama error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in one API call
        
        Args:
            texts: List of texts to embed (batch up to 32-64 at a time)
            
        Returns:
            List of embedding vectors
        """
        response = self.session.post(
            f"{self.ollama_url}/api/embed",
            json={
                "model": self.model,
                "input": texts  # Send list instead of single string
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Returns list of embeddings
        embeddings = data["embeddings"]
        total_tokens = data.get("prompt_eval_count", 0)
        
        return embeddings, total_tokens
    
    def embed_batch(self, texts: List[str], batch_size: int = 100) -> Tuple[List[List[float]], int]:
        """
        Generate embeddings for batch of texts using Ollama's batch API
        """
        all_embeddings = []
        max_tokens = 0

        total_tokens = 0              # running sum of tokens across all calls
        total_items = 0               # running count of all embedded texts

        pbar = tqdm(range(0, len(texts), batch_size), desc="Embedding batches")

        for i in pbar:
            batch_texts = texts[i:i + batch_size]

            response = self.session.post(
                f"{self.ollama_url}/api/embed",
                json={
                    "model": self.model,
                    "input": batch_texts
                }
            )
            response.raise_for_status()
            data = response.json()

            batch_embeddings = data["embeddings"]

            # tokens for this API call
            tokens_this_call = data.get("prompt_eval_count", 0)

            # running totals
            total_tokens += tokens_this_call
            total_items += len(batch_embeddings)

            # running average
            running_avg_tokens = total_tokens / total_items if total_items else 0

            all_embeddings.extend(batch_embeddings)

            pbar.set_postfix_str(
                f"Procc Items: {total_items} | "
                f"AVG Tokens: {running_avg_tokens:.1f}"
            )

        return all_embeddings, max_tokens

    def embed_batch_parallel(self, texts: List[str], batch_size: int = 32, max_workers: int = 4) -> Tuple[List[List[float]], int]:
        """
        Generate embeddings using parallel batch processing
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            max_workers: Number of parallel workers (match num_parallel in Ollama config)
            
        Returns:
            Tuple of (embeddings list, max tokens used)
        """
        # Split into batches
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        
        all_embeddings = []
        max_tokens = 0
        
        # Process batches in parallel
        pbar = tqdm(total=len(batches), desc="Embedding batches (parallel)")
        
        def process_batch(batch_texts):
            """Process single batch - runs in parallel"""
            response = self.session.post(
                f"{self.ollama_url}/api/embed",
                json={"model": self.model, "input": batch_texts},
                timeout=300
            )
            response.raise_for_status()
            data = response.json()
            
            return data["embeddings"], data.get("prompt_eval_count", 0)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batches
            futures = [executor.submit(process_batch, batch) for batch in batches]
            
            # Collect results as they complete
            for future in futures:
                batch_embeddings, tokens = future.result()
                all_embeddings.extend(batch_embeddings)
                
                if tokens > max_tokens:
                    max_tokens = tokens
                
                pbar.update(1)
                pbar.set_postfix_str(f"MAX TOKENS: {max_tokens}")
        
        pbar.close()
        return all_embeddings, max_tokens

    def keyword_search(self, query_text: str, collection_name: str, k: int = 10) -> List[Dict]:
        """Simple keyword search by filtering on text content"""
        collection = self.client.get_collection(name=collection_name)
        
        # Get all results (ChromaDB doesn't have native keyword search)
        # We'll do simple text matching
        results = collection.get()
        
        # Score by keyword presence
        query_terms = query_text.lower().split()
        scored = []
        
        for i, doc in enumerate(results['documents']):
            doc_lower = doc.lower()
            score = sum(1 for term in query_terms if term in doc_lower)
            if score > 0:
                scored.append({
                    'text': doc,
                    'metadata': results['metadatas'][i],
                    'keyword_score': score
                })
        
        # Sort by score and return top k
        scored.sort(key=lambda x: x['keyword_score'], reverse=True)
        return scored[:k]
    
    def _preprocess_query(self, query_text: str) -> str:
        """Remove question words to focus on core terms"""
        question_words = ['how', 'does', 'do', 'what', 'is', 'are', 'the', 'a', 'an']
        words = query_text.lower().split()
        filtered = [w for w in words if w not in question_words]
        return ' '.join(filtered) if filtered else query_text
    
    def hybrid_query(self, 
                    query_text: str, 
                    collection_name: str, 
                    k: int = 10,
                    max_book: Optional[int] = None) -> List[Dict]:
        """Enhanced retrieval: vector search + keyword boosting"""
        
        # Preprocess query for better embedding
        processed_query = self._preprocess_query(query_text)
        
        # Get more candidates than needed
        candidates = self.query(processed_query, collection_name, k=k*5, max_book=max_book)
        
        # Use ORIGINAL query for keyword matching
        query_terms = [term.lower() for term in query_text.split() if len(term) > 2]
        
        # Re-score with keyword boost
        for result in candidates:
            text_lower = result['text'].lower()
            
            # Count exact keyword matches
            keyword_matches = sum(1 for term in query_terms if term in text_lower)
            
            # Boost score if keywords present
            keyword_boost = keyword_matches * 0.1  # Adjust weight as needed
            result['boosted_score'] = (1.0 / (1 + result['distance'])) + keyword_boost
        
        # Re-sort by boosted score
        candidates.sort(key=lambda x: x['boosted_score'], reverse=True)
        
        return candidates[:k]
    
    def auto_query(self, query_text: str, k: int = 10, max_book: Optional[int] = None) -> List[Dict]:
        """Automatically route query to best collection"""
        
        query_lower = query_text.lower()
        
        # Check for specific magic terms FIRST (most specific)
        specific_magic = ['balefire', 'weave', 'saidin', 'saidar', 'angreal', 'channeling', 'ter\'angreal']
        if any(term in query_lower for term in specific_magic):
            collection = 'magic'
        
        # Then check for concept/explanation patterns
        elif any(term in query_lower for term in ['what is', 'explain', 'how does', 'what are']):
            collection = 'concepts'
        
        # Generic "power" or "channel" -> concepts (less specific)
        elif any(term in query_lower for term in ['power', 'channel']):
            collection = 'concepts'
        
        # Default to narrative
        else:
            collection = 'narrative'
        
        return self.hybrid_query(query_text, collection, k=k, max_book=max_book)

    def get_collection_count(self, collection_name: str) -> int:
        """Get document count in a collection"""
        collection = self.client.get_collection(name=collection_name)
        return collection.count()   
    
    def query(self, 
            query_text: str, 
            collection_name: str, 
            k: int = 10,
            max_book: Optional[int] = None) -> List[Dict]:
        """Query with post-filtering for temporal"""
        
        collection = self.client.get_collection(name=collection_name)
        query_embedding = self.embed_text(query_text)
        
        # Get more results than needed (for filtering)
        fetch_k = k * 3 if max_book is not None else k
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_k
        )
        
        # Format results
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        # Filter by temporal_order if needed
        if max_book is not None:
            filtered = []
            for r in formatted:
                temporal = r['metadata'].get('temporal_order', 'null')
                if temporal == 'null' or (temporal.isdigit() and int(temporal) <= max_book):
                    filtered.append(r)
                    if len(filtered) >= k:
                        break
            return filtered
        
        return formatted[:k]
