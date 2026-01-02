"""
Dragon's Codex - Retriever
Core retrieval logic for querying ChromaDB collections.
"""

from typing import Dict, List, Optional

import bm25s

from src.utils.config import get_config, get_embedding_manager_config
from src.utils.embedding.embedding_factory import create_embedding_manager
from src.utils.logger import get_logger
from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file
from src.utils.vector_store.vector_store_factory import VectorStoreFactory, VectorStoreType

logger = get_logger(__name__)


class Retriever:
    """Handles retrieval from ChromaDB collections"""

    def __init__(self, config=None):
        """
        Initialize Retriever

        Args:
            config: Config object (if None, loads from get_config())
        """
        if config is None:
            config = get_config()

        paths = get_paths()

        self.config = config

        self.vsm = create_embedding_manager(config.EMBEDDING_MANAGER, get_embedding_manager_config(config.EMBEDDING_MANAGER))

        # Initialize ChromaDB client
        self.vector_store_manager = VectorStoreFactory.create(store_type=VectorStoreType.CHROMA, path=paths.VECTOR_STORE_PATH, telemetry=config.CHROMA_TELEMETRY, allow_reset=False)

        # Load collections
        self.collections = {}
        self._load_collections()

        # === Load BM25 index once at startup ===
        bm25_dir = paths.BM25_INDEX_PATH
        print(f"Loading BM25 index from {bm25_dir}...")
        self.bm25_retriever = bm25s.BM25.load(bm25_dir, load_corpus=True)  # corpus needed for tokenization

        # Load mapping
        mapping = load_json_from_file(paths.FILE_BM25_MAPPING)
        self.bm25_chunk_ids = mapping["chunk_ids"]  # list[str] - your semantic chunk_id
        self.bm25_metadata = mapping["metadata"]  # list[dict] - full metadata per chunk

        print(f"BM25 loaded: {len(self.bm25_chunk_ids):,} chunks ready for hybrid search")

    def _load_collections(self):
        """Load all available ChromaDB collections"""
        try:
            # books collection (books)
            self.collections[self.config.CHROMA_COLLECTION_BOOKS] = self.vector_store_manager.get_collection(name=self.config.CHROMA_COLLECTION_BOOKS)
            logger.info(f"✅ Loaded collection: narrative ({self.collections[self.config.CHROMA_COLLECTION_BOOKS].count()} chunks)")

        except Exception as e:
            logger.warning(f"⚠️ Could not load narrative collection: {e}")

        try:
            # Narrative collection (books + chronology + chapter summaries)
            self.collections["narrative"] = self.vector_store_manager.get_collection(name=self.config.CHROMA_COLLECTION_NARRATIVE)
            logger.info(f"✅ Loaded collection: narrative ({self.collections['narrative'].count()} chunks)")

        except Exception as e:
            logger.warning(f"⚠️ Could not load narrative collection: {e}")

        try:
            # Reference collection (characters + concepts + magic + prophecies)
            self.collections["reference"] = self.vector_store_manager.get_collection(name=self.config.CHROMA_COLLECTION_REFERENCE)
            logger.info(f"✅ Loaded collection: reference ({self.collections['reference'].count()} chunks)")

        except Exception as e:
            logger.warning(f"⚠️ Could not load reference collection: {e}")

        if not self.collections:
            raise ValueError("❌ No ChromaDB collections found! Run embedding script first.")

    def query(
        self,
        query_text: str,
        collection_name: str = "books",
        top_k: int = 20,  # Final number of chunks returned to LLM
        temporal_limit: Optional[int] = None,
        number_expanded_terms: int = 0,  # Passed from expand_query_safe() — count of injected aliases
    ) -> Dict:
        """
        Hybrid query: Dense (Chroma) + BM25 → RRF fusion
        All tuning knobs are at the top for easy experimentation.
        """

        # ====================== TUNABLE PARAMETERS ======================
        DENSE_FETCH_MULTIPLIER = 5  # Balanced candidates (5x top_k)
        BM25_FETCH_MULTIPLIER = 5  # Balanced
        RRF_K = 50  # Balanced rank fusion
        BM25_BASE_WEIGHT = 1.0  # Default equal to dense
        BM25_HIGH_ALIAS_WEIGHT = 1.5  # Boost on term-heavy queries
        ALIAS_THRESHOLD = 4  # If expanded_terms > this → boost BM25
        # =================================================================

        # Dynamic weighting
        bm25_weight = BM25_BASE_WEIGHT
        if number_expanded_terms > ALIAS_THRESHOLD:
            bm25_weight = BM25_HIGH_ALIAS_WEIGHT  # Favor exact match on names/terms

        dense_fetch_k = top_k * DENSE_FETCH_MULTIPLIER
        bm25_k = top_k * BM25_FETCH_MULTIPLIER
        final_top_k = top_k

        if collection_name != "books":
            raise ValueError(f"Hybrid query only supports 'books' collection (got {collection_name})")

        collection = self.collections["books"]

        # ==================== 1. Dense Retrieval (Chroma) ====================
        logger.debug(f"Generating embedding for hybrid query: {query_text[:50]}...")
        embeddings, _, _, _ = self.vsm.embed_chunks(texts=[query_text], show_progress=False, prefix=self.vsm.get_manager_config()["EMBEDDING_MODEL"]["EMBEDDING_MODEL_SEARCH_PREFIX"])
        query_embedding = embeddings[0]

        where_filter = None
        if temporal_limit is not None:
            where_filter = {"temporal_order": {"$lte": temporal_limit}}

        results = collection.query(query_embeddings=[query_embedding], n_results=dense_fetch_k, where=where_filter)

        dense_chunks = []
        if results["ids"][0]:
            for i in range(len(results["ids"][0])):
                dense_chunks.append(
                    {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    }
                )

        # Post-filter: include timeless chunks (temporal_order=None) + enforce limit
        if temporal_limit is not None:
            dense_chunks = [c for c in dense_chunks if c["metadata"].get("temporal_order") is None or c["metadata"].get("temporal_order") <= temporal_limit]

        # ==================== 2. BM25 Retrieval ====================
        tokenized_batch = bm25s.tokenize([query_text], stemmer=None)
        query_tokens = tokenized_batch[0]

        bm25_scores, bm25_indices = self.bm25_retriever.retrieve(query_tokens, k=bm25_k)

        bm25_chunks = []
        if bm25_indices is not None and bm25_indices.size > 0:
            for idx, raw_score in zip(bm25_indices, bm25_scores):
                try:
                    score = float(raw_score)
                except (TypeError, ValueError):
                    score = 0.0

                if score <= 0:
                    continue

                chunk_id = self.bm25_chunk_ids[idx]
                metadata = self.bm25_metadata[idx]
                bm25_chunks.append(
                    {
                        "id": chunk_id,
                        "text": self.bm25_retriever.corpus[idx],
                        "distance": 1 / (score + 1e-6),
                        "metadata": metadata,
                    }
                )

        # Temporal filter for BM25
        if temporal_limit is not None:
            bm25_chunks = [
                c
                for c in bm25_chunks
                if c["metadata"].get("temporal_order") is None or (isinstance(c["metadata"].get("temporal_order"), (int, float)) and c["metadata"].get("temporal_order") <= temporal_limit)
            ]

        # ==================== 3. RRF Fusion ====================
        candidates = {}

        # Dense contribution
        for rank, chunk in enumerate(dense_chunks, 1):
            cid = chunk["id"]
            candidates[cid] = candidates.get(cid, 0) + 1 / (RRF_K + rank)

        # BM25 contribution (with dynamic weight)
        for rank, chunk in enumerate(bm25_chunks, 1):
            cid = chunk["id"]
            candidates[cid] = candidates.get(cid, 0) + bm25_weight / (RRF_K + rank)

        # Final ranking
        fused = sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:final_top_k]
        final_chunk_ids = [cid for cid, _ in fused]

        # Build final chunk list — prefer dense version when available
        final_chunks = []
        seen = set()
        for cid in final_chunk_ids:
            if cid in seen:
                continue
            seen.add(cid)
            chunk = next((c for c in dense_chunks if c["id"] == cid), None)
            if chunk is None:
                chunk = next((c for c in bm25_chunks if c["id"] == cid), None)
            if chunk:
                final_chunks.append(chunk)

        logger.info(f"Hybrid retrieved {len(final_chunks)} chunks (dense + BM25 fused) | aliases: {number_expanded_terms} → BM25 weight: {bm25_weight}")

        return {
            "query": query_text,
            "collection": collection_name,
            "top_k": top_k,
            "temporal_limit": temporal_limit,
            "results_count": len(final_chunks),
            "chunks": final_chunks,
        }

    def query_multiple_collections(
        self,
        query_text: str,
        collections: List[str],
        top_k_per_collection: Dict[str, int],
        temporal_limit: Optional[int] = None,
        number_expanded_terms: int = 0,
    ) -> Dict:
        """
        Query multiple collections and merge results

        Args:
            query_text: Query string
            collections: List of collection names to query
            top_k_per_collection: Dict mapping collection → top_k int
            temporal_limit: Temporal filter

        Returns:
            dict with merged results from all collections
        """
        all_chunks = []
        collection_counts = {}
        used_collections = []

        # Phase 2: Allow books + wiki_content_character
        allowed_collections = {
            self.config.CHROMA_COLLECTION_BOOKS,
            self.config.CHROMA_COLLECTION_CHARACTERS,  # wiki_content_character
        }

        for coll_name in collections:
            if coll_name not in allowed_collections:
                logger.warning(f"Blocked access to collection: {coll_name}")
                continue

            if coll_name not in self.collections:
                logger.warning(f"Skipping unknown collection: {coll_name}")
                continue

            # Get per-collection top_k
            top_k = top_k_per_collection.get(coll_name, 10)

            result = self.query(
                query_text=query_text,
                collection_name=coll_name,
                top_k=top_k,  # Now int
                temporal_limit=temporal_limit,
                number_expanded_terms=number_expanded_terms,
            )

            all_chunks.extend(result["chunks"])
            collection_counts[coll_name] = result["results_count"]
            used_collections.append(coll_name)

        if not all_chunks:
            logger.info("No chunks retrieved from allowed collections")
            return {"results": [], "total_results": 0}

        # Sort by distance
        all_chunks.sort(key=lambda x: x["distance"] if x["distance"] is not None else 999)

        logger.info(f"Retrieved {len(all_chunks)} total chunks from {used_collections}")

        return {
            "query": query_text,
            "collections": used_collections,
            "top_k_per_collection": {c: top_k_per_collection.get(c, 10) for c in used_collections},
            "temporal_limit": temporal_limit,
            "total_results": len(all_chunks),
            "collection_counts": collection_counts,
            "chunks": all_chunks,
        }

    def get_collection_stats(self) -> Dict:
        """Get statistics about loaded collections"""
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = {"count": collection.count(), "name": collection.name}
        return stats
