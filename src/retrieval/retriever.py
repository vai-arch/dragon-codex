"""
Dragon's Codex - Retriever
Core retrieval logic for querying ChromaDB collections.
"""

from typing import Dict, List, Optional

from src.utils.config import get_config, get_embedding_manager_config
from src.utils.embedding.embedding_factory import create_embedding_manager
from src.utils.logger import get_logger
from src.utils.paths import get_paths
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

    def query(self, query_text: str, collection_name: str = "narrative", top_k: int = 10, temporal_limit: Optional[int] = None) -> Dict:
        """
        Query a ChromaDB collection

        Args:
            query_text: Query string
            collection_name: 'narrative' or 'reference'
            top_k: Number of results to return
            temporal_limit: If set, only return chunks up to this book number

        Returns:
            dict with:
                - query: Original query text
                - collection: Collection queried
                - top_k: Number requested
                - temporal_limit: Temporal filter applied
                - results_count: Actual results returned
                - chunks: List of retrieved chunks with metadata
        """
        if collection_name not in self.collections:
            raise ValueError(f"❌ Collection not found: {collection_name}")

        collection = self.collections[collection_name]

        # Generate query embedding
        logger.debug(f"🔍 Generating embedding for query: {query_text[:50]}...")
        embeddings, _, _, _ = self.vsm.embed_chunks(texts=[query_text], show_progress=False, prefix=self.vsm.get_manager_config()["EMBEDDING_MODEL"]["EMBEDDING_MODEL_SEARCH_PREFIX"])
        query_embedding = embeddings[0]

        # Build ChromaDB where filter for temporal limit
        # Note: ChromaDB doesn't support filtering for null/None values well
        # We'll fetch all results and filter in post-processing if needed
        where_filter = None
        if temporal_limit is not None:
            # Only filter for chunks WITH temporal_order <= limit
            # Chunks without temporal_order will need post-filtering
            where_filter = {"temporal_order": {"$lte": temporal_limit}}

        # Query ChromaDB
        logger.debug(f"🔍 Querying collection: {collection_name}, top_k: {top_k}")

        # If temporal limit set, we need to fetch MORE results because we'll post-filter
        # to include chunks with temporal_order=None
        fetch_k = top_k * 3 if temporal_limit is not None else top_k

        results = collection.query(query_embeddings=[query_embedding], n_results=fetch_k, where=where_filter)

        # Parse results
        chunks = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                chunk = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else None,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                }
                chunks.append(chunk)

        # Post-filter: If temporal_limit set, also include chunks with temporal_order=None
        # (these are timeless wiki content like definitions)
        if temporal_limit is not None:
            filtered_chunks = []
            for chunk in chunks:
                t_order = chunk["metadata"].get("temporal_order")
                # Include if: temporal_order <= limit OR temporal_order is None
                if t_order is None or t_order <= temporal_limit:
                    filtered_chunks.append(chunk)

            # Trim to requested top_k
            chunks = filtered_chunks[:top_k]

        logger.info(f"✅ Retrieved {len(chunks)} chunks from {collection_name}")

        return {"query": query_text, "collection": collection_name, "top_k": top_k, "temporal_limit": temporal_limit, "results_count": len(chunks), "chunks": chunks}

    def query_multiple_collections(self, query_text: str, collections: List[str] = ["narrative", "reference"], top_k_per_collection: int = 5, temporal_limit: Optional[int] = None) -> Dict:
        """
        Query multiple collections and merge results

        Args:
            query_text: Query string
            collections: List of collection names to query
            top_k_per_collection: Number of results per collection
            temporal_limit: Temporal filter

        Returns:
            dict with merged results from all collections
        """
        all_chunks = []
        collection_counts = {}

        # Phase 1 safety filter
        allowed_collections = {"books"}  # or {"books"}
        filtered_collections = [c for c in collections if c in allowed_collections]

        if not filtered_collections:
            logger.error(f"No allowed collections found! Requested: {collections}")
            return {"results": [], "total_results": 0}

        if set(collections) != set(filtered_collections):
            logger.warning(f"Blocked access to non-book collections: {set(collections) - set(filtered_collections)}")
            raise ValueError(f"Blocked access to non-book collections: {set(collections) - set(filtered_collections)}")

        for coll_name in collections:
            if coll_name not in self.collections:
                logger.warning(f"⚠️ Skipping unknown collection: {coll_name}")
                continue

            result = self.query(query_text=query_text, collection_name=coll_name, top_k=top_k_per_collection, temporal_limit=temporal_limit)

            all_chunks.extend(result["chunks"])
            collection_counts[coll_name] = result["results_count"]

        # Sort by distance (lower is better)
        all_chunks.sort(key=lambda x: x["distance"] if x["distance"] is not None else 999)

        logger.info(f"✅ Retrieved {len(all_chunks)} total chunks across {len(collections)} collections")

        return {
            "query": query_text,
            "collections": collections,
            "top_k_per_collection": top_k_per_collection,
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
