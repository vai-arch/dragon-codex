"""
Semantic Chunker - Groups paragraphs based on semantic similarity
Supports any embedding model through abstract interface
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple

import numpy as np
from tqdm import tqdm


class EmbeddingProvider(ABC):
    """Abstract interface for embedding models"""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each is List[float])
        """
        pass


class OllamaEmbedder(EmbeddingProvider):
    """Ollama-based embeddings (current implementation)"""

    def __init__(self, config=None):
        if config is None:
            from src.utils.config import get_config

            config = get_config()

        self.config = config
        self.ollama_url = config.OLLAMA_BASE_URL
        self.model = config.EMBEDDING_MODEL

        import requests

        self.session = requests.Session()

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama"""
        all_embeddings = []

        for text in texts:
            response = self.session.post(
                f"{self.ollama_url}/api/embed",
                json={
                    "model": self.model,
                    "input": text,
                },
            )
            response.raise_for_status()
            data = response.json()
            all_embeddings.extend(data["embeddings"])

        return all_embeddings


class SentenceTransformerEmbedder(EmbeddingProvider):
    """Sentence Transformers embeddings (future use)"""

    def __init__(self, model_name: str = "C:\\Users\\Usuario\\Documents\\_AI\\codex-forge\\models\\finetuned_v1\\final_model", trust_remote_code: bool = True):
        # def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5", trust_remote_code: bool = True):
        """
        Initialize sentence transformer model.

        Args:
            model_name: HuggingFace model name or path to local model
        """
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name, trust_remote_code=trust_remote_code)
        except ImportError:
            raise ImportError("Install sentence-transformers: pip install sentence-transformers")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using SentenceTransformer"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


class SemanticChunker:
    """
    Semantic-aware sequential chunker.

    Groups consecutive paragraphs into chunks based on:
    1. Semantic similarity between consecutive paragraphs
    2. Maximum chunk size limit

    Breaks chunks when similarity drops below threshold OR max size reached.
    """

    def __init__(self, embedder: EmbeddingProvider, max_chunk_chars: int = 6000, similarity_threshold: float = 0.75, overlap_percent: float = 0.10, show_progress: bool = True):
        """
        Initialize semantic chunker.

        Args:
            embedder: Embedding provider (Ollama, SentenceTransformer, etc.)
            max_chunk_chars: Maximum characters per chunk
            similarity_threshold: Cosine similarity threshold for grouping (0-1)
            overlap_percent: Percentage overlap between chunks (0-1)
            show_progress: Show progress bars during processing
        """
        self.embedder = embedder
        self.max_chunk_chars = max_chunk_chars
        self.similarity_threshold = similarity_threshold
        self.overlap_percent = overlap_percent
        self.show_progress = show_progress

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _calculate_consecutive_similarities(self, embeddings: List[List[float]]) -> List[float]:
        """
        Calculate similarity between each consecutive pair of embeddings.

        Returns:
            List of similarity scores (length = len(embeddings) - 1)
        """
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)

        return similarities

    def _get_overlap_paragraphs(self, paragraphs: List[str], chunk_end_idx: int) -> List[str]:
        """
        Get overlap paragraphs from end of current chunk.

        Args:
            paragraphs: List of all paragraphs
            chunk_end_idx: Index where current chunk ends

        Returns:
            List of paragraphs to overlap into next chunk
        """
        if chunk_end_idx >= len(paragraphs):
            return []

        # Calculate target overlap size
        overlap_chars = 0
        overlap_paras = []
        target_overlap_chars = int(self.max_chunk_chars * self.overlap_percent)

        # Walk backwards from chunk_end_idx
        for i in range(chunk_end_idx - 1, -1, -1):
            para_len = len(paragraphs[i])
            if overlap_chars + para_len <= target_overlap_chars:
                overlap_paras.insert(0, paragraphs[i])
                overlap_chars += para_len
            else:
                break

        return overlap_paras

    def chunk_paragraphs(self, paragraphs: List[str], verbose: bool = False) -> Tuple[List[str], dict]:
        """
        Group consecutive paragraphs into semantic chunks.

        Algorithm:
        1. Embed all paragraphs
        2. Calculate similarity between consecutive paragraphs
        3. Group paragraphs while similarity > threshold AND size < max
        4. Break chunk at semantic boundary or size limit
        5. Add overlap from previous chunk

        Args:
            paragraphs: List of paragraph strings
            verbose: Print detailed chunking decisions

        Returns:
            Tuple of:
                - List of chunk strings (grouped paragraphs)
                - Statistics dict
        """
        if not paragraphs:
            return [], {"total_paragraphs": 0, "total_chunks": 0}

        start_time = datetime.now()

        # Step 1: Embed all paragraphs
        print("\n Embedding paragraphs for semantic analysis...")
        embeddings = self.embedder.embed(paragraphs)

        # Step 2: Calculate consecutive similarities
        similarities = self._calculate_consecutive_similarities(embeddings)

        # Step 3: Group into chunks
        chunks = []
        current_chunk_paras = []
        current_chunk_chars = 0

        breaks_by_similarity = 0
        breaks_by_size = 0

        pbar = tqdm(enumerate(paragraphs), total=len(paragraphs), desc="Creating semantic chunks", disable=not self.show_progress)

        for i, paragraph in pbar:
            para_chars = len(paragraph)

            # Check if adding this paragraph would exceed max size
            would_exceed = (current_chunk_chars + para_chars) > self.max_chunk_chars

            # Check semantic similarity with previous paragraph
            low_similarity = False
            if i > 0 and i - 1 < len(similarities):
                similarity = similarities[i - 1]
                low_similarity = similarity < self.similarity_threshold

                if verbose and low_similarity:
                    print(f"\n  âš ï¸  Low similarity at para {i}: {similarity:.3f}")

            # Decision: Start new chunk?
            if current_chunk_paras and (would_exceed or low_similarity):
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk_paras)
                chunks.append(chunk_text)

                # Track break reason
                if low_similarity:
                    breaks_by_similarity += 1
                    if verbose:
                        print(f" Break by similarity (chunk {len(chunks)})")
                else:
                    breaks_by_size += 1
                    if verbose:
                        print(f" Break by size (chunk {len(chunks)})")

                # Get overlap from previous chunk
                overlap_paras = self._get_overlap_paragraphs(paragraphs, i)

                # Start new chunk with overlap + current paragraph
                current_chunk_paras = overlap_paras + [paragraph]
                current_chunk_chars = sum(len(p) for p in current_chunk_paras)
            else:
                # Add to current chunk
                current_chunk_paras.append(paragraph)
                current_chunk_chars += para_chars

        # Add final chunk
        if current_chunk_paras:
            chunk_text = "\n\n".join(current_chunk_paras)
            chunks.append(chunk_text)

        # Statistics
        total_time = datetime.now() - start_time
        chunk_chars = [len(c) for c in chunks]

        stats = {
            "total_paragraphs": len(paragraphs),
            "total_chunks": len(chunks),
            "avg_chunk_chars": sum(chunk_chars) / len(chunk_chars) if chunks else 0,
            "min_chunk_chars": min(chunk_chars) if chunks else 0,
            "max_chunk_chars": max(chunk_chars) if chunks else 0,
            "breaks_by_similarity": breaks_by_similarity,
            "breaks_by_size": breaks_by_size,
            "processing_time_seconds": total_time.total_seconds(),
        }

        return chunks, stats


def test_semantic_chunker():
    """Test the semantic chunker with sample paragraphs"""

    # Sample paragraphs simulating chapter content
    sample_paragraphs = [
        # Scene 1: Battle description (high similarity)
        "The Trollocs charged across the field, their twisted forms howling in the morning light.",
        "Perrin raised his hammer, feeling the wolf rage building inside him.",
        "He struck the first Trolloc with devastating force, bones shattering.",
        # Scene 2: Transition to different scene (low similarity break)
        "Meanwhile, in the White Tower, Egwene sat in the Amyrlin's study.",
        "The weight of leadership pressed down on her shoulders.",
        "She needed to unite the Aes Sedai before it was too late.",
        # Scene 3: Political discussion (high similarity)
        "The Hall of the Tower was filled with tension.",
        "Sisters from different Ajahs glared at each other across the chamber.",
        "Egwene knew she had to find common ground, or the Tower would shatter.",
    ]

    # Test with Ollama (if available)
    print("Testing SemanticChunker...")
    print(f"Sample paragraphs: {len(sample_paragraphs)}")

    try:
        # embedder = OllamaEmbedder()
        embedder = SentenceTransformerEmbedder()
        chunker = SemanticChunker(
            embedder=embedder,
            max_chunk_chars=500,  # Small for testing
            similarity_threshold=0.75,
            overlap_percent=0.10,
            show_progress=True,
        )

        chunks, stats = chunker.chunk_paragraphs(sample_paragraphs, verbose=True)

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Breaks by similarity: {stats['breaks_by_similarity']}")
        print(f"Breaks by size: {stats['breaks_by_size']}")
        print(f"Avg chunk size: {stats['avg_chunk_chars']:.0f} chars")
        print(f"Processing time: {stats['processing_time_seconds']:.2f}s")

        print(" CHUNKS:")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n--- Chunk {i} ({len(chunk)} chars) ---")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)

    except Exception as e:
        print(f"Test failed: {e}")
        print("(Ollama might not be running)")


if __name__ == "__main__":
    test_semantic_chunker()
