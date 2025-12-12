"""
Embedding handling
"""

from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple
from tqdm import tqdm

from src.utils.util_statistics import progress_bar


class VectorStoreManager:
    """Manages embeddings and vector storage"""
    
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
        Generate embeddings for a batch of texts and return statistics.

        This function processes a list of input texts, generates embeddings
        for each text (using a model such as Ollama), and computes token-usage
        and performance metrics across the full batch.

        Args:
            texts (List[str]):  
                List of input text strings to embed.
            batch_size (int):  
                Number of items processed per API call.

        Returns:
            tuple:
                embeddings (List[List[float]]):  
                    The embedding vector for each input text, in order.
                
                avg_tokens (float):  
                    The average number of tokens consumed per batch request.
                
                max_tokens (int):  
                    The maximum token usage observed across all batch calls.
                
                total_time (float):  
                    Total processing time (in seconds) for generating all embeddings.
        """

        start_time = datetime.now()

        max_tokens = 0
        count =0

        pbar = tqdm(texts, desc="Embedding chunks")

        for text in pbar:
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
            this_chunk_tokens = data.get("prompt_eval_count", 0)

            # update max
            if this_chunk_tokens > max_tokens:
                max_tokens = this_chunk_tokens

            # update totals for average
            total_tokens += this_chunk_tokens
            count += 1

            avg_tokens = total_tokens / count

            pbar.set_postfix_str(f"MAX: {max_tokens} | AVG: {avg_tokens:.1f}")

        total_time = datetime.now() - start_time

        return embeddings, avg_tokens, max_tokens, total_time
    
    def embed_batch(self, texts: List[str], batch_size: int = 100, show_progress: bool = True) -> Tuple[List[List[float]], int]:
        """
       Generate embeddings for a batch of texts and return statistics.

        This function processes a list of input texts, generates embeddings
        for each text (using a model such as Ollama), and computes token-usage
        and performance metrics across the full batch.

        Args:
            texts (List[str]):  
                List of input text strings to embed.
            batch_size (int):  
                Number of items processed per API call.

        Returns:
            tuple:
                embeddings (List[List[float]]):  
                    The embedding vector for each input text, in order.
                
                avg_tokens (float):  
                    The average number of tokens consumed per batch request.
                
                max_tokens (int):  
                    The maximum token usage observed across all batch calls.
                
                total_time (float):  
                    Total processing time (in seconds) for generating all embeddings.
        """
        start_time = datetime.now()

        all_embeddings = []
        max_tokens = -1

        total_tokens = 0              # running sum of tokens across all calls
        total_items = 0               # running count of all embedded texts

        # pbar = tqdm(range(0, len(texts), batch_size), desc="Embedding batches")

        pbar = progress_bar(range(0, len(texts), batch_size), enable=show_progress, desc="Embedding batches")

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
            avg_tokens = total_tokens / total_items if total_items else 0

            all_embeddings.extend(batch_embeddings)
            
            if hasattr(pbar, "set_postfix_str"):
                pbar.set_postfix_str(
                    f"Procc Items: {total_items} | "
                    f"AVG Tokens: {avg_tokens:.1f}"
                )

        total_time = datetime.now() - start_time

        return all_embeddings, avg_tokens, max_tokens, total_time

    def embed_batch_parallel(self, texts: List[str], batch_size: int = 100, max_workers: int = 4) -> Tuple[List[List[float]], int]:
        """
        Generate embeddings for a batch of texts and return statistics.

        This function processes a list of input texts, generates embeddings
        for each text (using a model such as Ollama), and computes token-usage
        and performance metrics across the full batch.

        Args:
            texts (List[str]):  
                List of input text strings to embed.
            batch_size (int):  
                Number of items processed per API call.

        Returns:
            tuple:
                embeddings (List[List[float]]):  
                    The embedding vector for each input text, in order.
                
                avg_tokens (float):  
                    The average number of tokens consumed per batch request.
                
                max_tokens (int):  
                    The maximum token usage observed across all batch calls.
                
                total_time (float):  
                    Total processing time (in seconds) for generating all embeddings.
        """

        start_time = datetime.now()

        # Split into batches
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        
        all_embeddings = []
        avg_tokens = 0
        max_tokens = -1
        
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
                
                if tokens > avg_tokens:
                    avg_tokens = tokens
                
                pbar.update(1)
                pbar.set_postfix_str(f"MAX TOKENS: {avg_tokens}")
        
        pbar.close()

        total_time = datetime.now() - start_time
        
        return all_embeddings, avg_tokens, max_tokens, total_time
