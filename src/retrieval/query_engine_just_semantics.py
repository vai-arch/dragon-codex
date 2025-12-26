"""
Dragon's Codex - Query Engine
Handles query processing, classification, and collection routing.
"""

from typing import Dict, Optional, Tuple

from src.retrieval.dynamic_query_classifier import DynamicQueryClassifier
from src.retrieval.retriever import Retriever
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.paths import get_paths

logger = get_logger(__name__)


class QueryEngine:
    """
    Query processing and routing engine.
    Classifies queries and routes to appropriate collections.
    """

    def __init__(self, config=None, paths=None):
        """
        Initialize Query Engine

        Args:
            config: Config object (if None, loads from get_config())
            paths: Paths object (if None, loads from get_paths())
        """
        if config is None:
            config = get_config()
        if paths is None:
            paths = get_paths()

        self.config = config
        self.paths = paths
        self.retriever = Retriever(config)

        # Initialize dynamic classifier (learns from indexes)
        self.classifier = DynamicQueryClassifier(config, paths)

    def classify_query(self, query_text: str) -> Tuple[str, float]:
        """
        Classify query into category using dynamic classifier

        Args:
            query_text: Query string

        Returns:
            tuple: (category, confidence)
        """
        return self.classifier.classify_query(query_text)

    def route_query(
        self,
        query_text: str,
        category: Optional[str] = None,
        temporal_limit: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        PHASE 1 ONLY: Force books-only retrieval
        Disable classifier and reference/wiki collections
        """
        # TODO PHASE 1A Hard-code for Phase 1 safety
        book_collection_name = "books"  # ← Change if your book collection has a different name (e.g., "books")

        logger.info("🔒 PHASE 1 MODE: Forcing retrieval from books only (no wiki/reference collections)")

        return {
            "category": "phase1_books_only",  # Clear indicator
            "confidence": 1.0,
            "collections_used": [book_collection_name],
            "top_k_per_collection": 10,  # Keep consistent with baseline
            "routing_strategy": "phase1_books_only",
            "temporal_limit": temporal_limit,
        }

    def route_query_phase1c(self, query_text: str, category: Optional[str] = None, temporal_limit: Optional[int] = None) -> Dict[str, any]:
        """
        Route query to appropriate collection(s)

        Args:
            query_text: Query string
            category: Pre-classified category (if None, auto-classify)
            temporal_limit: Temporal filter

        Returns:
            dict with:
                - category: Detected category
                - confidence: Classification confidence
                - collections_used: Which collections were queried
                - routing_strategy: How collections were chosen
        """
        # THIS IS JUST FOR PHASE I
        if category is None:
            # Timeline queries: Narrative focus (chronology pages + book events)
            collections = ["narrative"]
            top_k = 10
            strategy = "phase_I"
            confidence = 1.0
        else:
            # Classify if not provided
            if category is None:
                category, confidence = self.classify_query(query_text)
            else:
                confidence = 1.0

            # Route based on category
            if category == "character":
                # Character queries: Use both collections (wiki has character pages, books have arcs)
                collections = ["narrative", "reference"]
                top_k = 5  # 5 per collection = 10 total
                strategy = "both_collections_character_focus"

            elif category == "concept":
                # Concept queries: Reference first (wiki definitions), narrative second
                collections = ["reference", "narrative"]
                top_k = 5
                strategy = "reference_primary_narrative_secondary"

            elif category == "magic":
                # Magic queries: Reference (magic system index) + narrative (examples)
                collections = ["reference", "narrative"]
                top_k = 5
                strategy = "reference_primary_narrative_secondary"

            elif category == "prophecy":
                # Prophecy queries: Reference (prophecy index) + narrative (events)
                collections = ["reference", "narrative"]
                top_k = 5
                strategy = "reference_primary_narrative_secondary"

            elif category == "timeline":
                # Timeline queries: Narrative focus (chronology pages + book events)
                collections = ["narrative"]
                top_k = 10
                strategy = "narrative_only_temporal_focus"

            else:  # 'general'
                # General queries: Both collections, balanced
                collections = ["narrative", "reference"]
                top_k = 5
                strategy = "balanced_both_collections"

        logger.info(f"🔀 Routing: {category} → {strategy}")

        return {"category": category, "confidence": confidence, "collections_used": collections, "top_k_per_collection": top_k, "routing_strategy": strategy, "temporal_limit": temporal_limit}

    def execute_query(self, query_text: str, temporal_limit: Optional[int] = None, force_category: Optional[str] = None, top_k: Optional[int] = None) -> Dict:
        """
        Execute complete query pipeline: classify → route → retrieve

        Args:
            query_text: Query string
            temporal_limit: Temporal filter (book number)
            force_category: Override auto-classification
            top_k: Override default top_k

        Returns:
            dict with:
                - query: Original query
                - category: Detected/forced category
                - routing: Routing information
                - results: Retrieved chunks
                - metadata: Query metadata
        """
        logger.info(f"\n{'=' * 70}")
        logger.info(f"🔍 QUERY: {query_text}")
        logger.info(f"{'=' * 70}")

        # Route query
        routing = self.route_query(query_text=query_text, category=force_category, temporal_limit=temporal_limit)

        # Override top_k if specified
        if top_k is not None:
            routing["top_k_per_collection"] = top_k

        # Execute retrieval
        retrieval_result = self.retriever.query_multiple_collections(
            query_text=query_text, collections=routing["collections_used"], top_k_per_collection=routing["top_k_per_collection"], temporal_limit=temporal_limit
        )

        # Combine results
        result = {
            "query": query_text,
            "category": routing["category"],
            "confidence": routing["confidence"],
            "routing": routing,
            "results": retrieval_result,
            "metadata": {
                "total_chunks_retrieved": retrieval_result["total_results"],
                "collections_queried": routing["collections_used"],
                "temporal_limit_applied": temporal_limit is not None,
                "routing_strategy": routing["routing_strategy"],
            },
        }

        logger.info(f"✅ Query complete: {result['metadata']['total_chunks_retrieved']} chunks retrieved")

        return result

    def get_stats(self) -> Dict:
        """Get query engine statistics"""
        return {"collections": self.retriever.get_collection_stats(), "classifier": self.classifier.get_stats()}
