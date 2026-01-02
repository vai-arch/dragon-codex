"""
Dragon's Codex - Query Engine
Handles query processing, classification, and collection routing.
"""

from typing import Dict, Optional

import torch

from src.retrieval.retriever import Retriever
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.paths import get_paths
from src.utils.query_classification.query_classifier import QueryClassifier
from src.utils.util_files_functions import load_json_from_file

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

        self.character_index = load_json_from_file(paths.FILE_CHARACTER_INDEX)
        self.classifier = QueryClassifier(device=0 if torch.cuda.is_available() else -1)

    def route_query(
        self,
        query_text: str,
        category: Optional[str] = None,
        temporal_limit: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Phase 2: Intelligent routing with classifier and character priority
        - Classify query (or override)
        - Character: wiki_content_character primary + books fallback + alias expansion
        - Other: books default (expand later)
        - Temporal limit preserved
        """

        # Classification
        if category is None:
            classification = self.classifier.classify(query_text)
            category = classification["category"]
            confidence = classification["confidence"]
        else:
            confidence = 1.0

        logger.info(f"Routing query | Category: {category} (conf: {confidence:.2f}) | Temporal limit: {temporal_limit}")

        # Default
        collections = []
        top_k_per = {}
        expanded_query = query_text
        routing_strategy = "default"

        if category == "character":
            # Alias expansion for better retrieval
            query_lower = query_text.lower()
            for char_data in self.character_index.values():
                primary = char_data["primary_name"].lower()
                aliases = [a.lower() for a in char_data.get("aliases", [])]
                all_names = [primary] + aliases
                if any(name in query_lower for name in all_names):
                    expanded_query = f"{query_text} {char_data['primary_name']} {' '.join(char_data.get('aliases', []))}"
                    break

            # Primary: wiki characters (narrative arcs)
            collections.append(self.config.CHROMA_COLLECTION_CHARACTERS)
            top_k_per[self.config.CHROMA_COLLECTION_CHARACTERS] = 15

            # Fallback: books (event details)
            collections.append(self.config.CHROMA_COLLECTION_BOOKS)
            top_k_per[self.config.CHROMA_COLLECTION_BOOKS] = 10

            routing_strategy = "character_wiki_primary"
        else:
            # Non-character (concept, prophecy, plot_event, etc.) — books for now
            collections.append("books")
            top_k_per["books"] = 20
            routing_strategy = "non_character_books"

        return {
            "category": category,
            "confidence": confidence,
            "collections_used": collections,
            "top_k_per_collection": top_k_per,
            "routing_strategy": routing_strategy,
            "temporal_limit": temporal_limit,
            "expanded_query": expanded_query,
        }

    def execute_query(
        self,
        query_text: str,
        temporal_limit: Optional[int] = None,
        force_category: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> Dict:
        """
        Execute complete query pipeline: classify → route → retrieve

        Args:
            query_text: Original query string
            temporal_limit: Book limit for spoiler control
            force_category: Override classifier
            top_k: Override per-collection top_k

        Returns:
            dict with query results, routing, metadata
        """
        logger.info(f"\n{'=' * 70}")
        logger.info(f"🔍 QUERY: {query_text}")
        if temporal_limit is not None:
            logger.info(f"⏳ Temporal limit: up to book {temporal_limit}")
        logger.info(f"{'=' * 70}")

        # Phase 2 routing with classifier + alias expansion
        routing = self.route_query(
            query_text=query_text,
            category=force_category,
            temporal_limit=temporal_limit,
        )

        # Use expanded query from routing (includes aliases)
        final_query = routing.get("expanded_query", query_text)

        logger.info(f"📝 Final query (with expansion): {final_query}")
        logger.info(f"🎯 Category: {routing['category']} (conf: {routing['confidence']:.2f})")
        logger.info(f"🗂️ Collections: {routing['collections_used']}")
        logger.info(f"🔢 Top-k: {routing['top_k_per_collection']}")
        logger.info(f"🛡️ Routing strategy: {routing['routing_strategy']}")

        # Override top_k if user specified
        if top_k is not None:
            routing["top_k_per_collection"] = {coll: top_k for coll in routing["collections_used"]}

        # Execute retrieval
        retrieval_result = self.retriever.query_multiple_collections(
            query_text=final_query,
            collections=routing["collections_used"],
            top_k_per_collection=routing["top_k_per_collection"],
            temporal_limit=temporal_limit,
        )

        # Final result
        result = {
            "query": query_text,  # Original
            "expanded_query": final_query,
            "category": routing["category"],
            "confidence": routing["confidence"],
            "routing": routing,
            "results": retrieval_result,
            "metadata": {
                "total_chunks_retrieved": retrieval_result["total_results"],
                "collections_queried": routing["collections_used"],
                "temporal_limit_applied": temporal_limit,
                "routing_strategy": routing["routing_strategy"],
            },
        }

        logger.info(f"✅ Query complete: {result['metadata']['total_chunks_retrieved']} chunks retrieved")

        return result

    def get_stats(self) -> Dict:
        """Get query engine statistics"""
        return {"collections": self.retriever.get_collection_stats(), "classifier": self.classifier.get_stats()}
