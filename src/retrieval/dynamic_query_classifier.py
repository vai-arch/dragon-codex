"""
Dragon's Codex - Dynamic Query Classifier
Builds classification patterns from existing indexes (no hardcoding!)
"""

import re
from typing import Dict, List, Set, Tuple

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file

logger = get_logger(__name__)


class DynamicQueryClassifier:
    """
    Query classifier that learns from existing data indexes.
    No hardcoded terms - everything extracted from character_index.json,
    magic_system_index.json, etc.
    """

    def __init__(self, config=None, paths=None):
        """Initialize classifier and load indexes"""
        if config is None:
            config = get_config()
        if paths is None:
            paths = get_paths()

        self.config = config
        self.paths = paths

        # Load indexes
        self.character_index = self._load_index(paths.FILE_CHARACTER_INDEX)
        self.magic_index = self._load_index(paths.FILE_MAGIC_SYSTEM_INDEX)
        self.prophecy_index = self._load_index(paths.FILE_PROPHECY_INDEX)
        self.concept_index = self._load_index(paths.FILE_CONCEPT_INDEX)

        # Extract terms from indexes
        self.character_names = self._extract_character_names()
        self.magic_terms = self._extract_magic_terms()
        self.prophecy_terms = self._extract_prophecy_terms()
        self.location_terms = self._extract_location_terms()

        # Build patterns dynamically
        self.patterns = self._build_patterns()

        logger.info("✅ Dynamic classifier initialized")
        logger.info(f"   Characters: {len(self.character_names)}")
        logger.info(f"   Magic terms: {len(self.magic_terms)}")
        logger.info(f"   Prophecy terms: {len(self.prophecy_terms)}")
        logger.info(f"   Locations: {len(self.location_terms)}")

    def _load_index(self, filepath) -> Dict:
        """Load index file safely"""
        try:
            return load_json_from_file(filepath, log=False)
        except Exception as e:
            logger.warning(f"Could not load {filepath}: {e}")
            return {}

    def _extract_character_names(self) -> Set[str]:
        """Extract all character names and aliases from character_index"""
        names = set()

        if not self.character_index:
            return names

        for char_name, char_data in self.character_index.items():
            # Add main name
            names.add(char_name.lower())

            # Add aliases
            if isinstance(char_data, dict):
                aliases = char_data.get("aliases", [])
                if isinstance(aliases, list):
                    names.update(a.lower() for a in aliases)

                # Add titles (optional - might be too broad)
                titles = char_data.get("titles", [])
                if isinstance(titles, list):
                    names.update(t.lower() for t in titles if len(t.split()) <= 3)

        return names

    def _extract_magic_terms(self) -> Set[str]:
        """Extract magic system terms from magic_system_index"""
        terms = set()

        if not self.magic_index:
            return terms

        for term_name, term_data in self.magic_index.items():
            terms.add(term_name.lower())

            # Add related terms
            if isinstance(term_data, dict):
                related = term_data.get("related_terms", [])
                if isinstance(related, list):
                    terms.update(r.lower() for r in related)

        return terms

    def _extract_prophecy_terms(self) -> Set[str]:
        """Extract prophecy-related terms from prophecy_index"""
        terms = set()

        if not self.prophecy_index:
            return terms

        for prophecy_name in self.prophecy_index.keys():
            terms.add(prophecy_name.lower())

        # Add common prophecy keywords (minimal hardcoding)
        terms.update(["foretelling", "viewing", "prophecy", "prophecies"])

        return terms

    def _extract_location_terms(self) -> Set[str]:
        """Extract location names from concept_index"""
        locations = set()

        if not self.concept_index:
            return locations

        for concept_name, concept_data in self.concept_index.items():
            if isinstance(concept_data, dict):
                # Check if it's a location (you could add location type to index)
                concept_type = concept_data.get("type", "").lower()
                if "location" in concept_type or "place" in concept_type or "city" in concept_type:
                    locations.add(concept_name.lower())

        return locations

    def _build_patterns(self) -> Dict[str, List[str]]:
        """
        Build classification patterns dynamically from extracted terms.
        Only minimal structural patterns are hardcoded.
        """

        # Escape regex special characters in terms
        def escape_terms(terms):
            return [re.escape(t) for t in terms]

        # Build character name pattern
        char_pattern = f"({'|'.join(escape_terms(list(self.character_names)[:100]))})"  # Limit to 100 most common

        # Build magic term pattern
        magic_pattern = f"({'|'.join(escape_terms(list(self.magic_terms)))})"

        # Build prophecy term pattern
        prophecy_pattern = f"({'|'.join(escape_terms(list(self.prophecy_terms)))})"

        # Build location pattern
        location_pattern = f"({'|'.join(escape_terms(list(self.location_terms)[:50]))})"

        patterns = {
            "character": [
                # Structural patterns (minimal hardcoding)
                r"\b(who is|describe|tell me about|what happens to)\b",
                r"\b(character|person|people)\b",
                r"\b(relationship|bond|warder)\b",
            ],
            "concept": [
                # Structural patterns
                r"\b(what is|explain|define|describe)\b",
                # Location terms (from index)
                location_pattern if location_pattern != "()" else None,
            ],
            "magic": [
                # Structural patterns
                r"\b(channeling|weave|flow|power)\b",
                # Magic terms (from index)
                magic_pattern if magic_pattern != "()" else None,
            ],
            "prophecy": [
                # Prophecy terms (from index)
                prophecy_pattern if prophecy_pattern != "()" else None,
                # Structural patterns
                r"\b(dragon reborn|pattern)\b",
            ],
            "timeline": [
                # Structural patterns (unavoidable - these are English constructs)
                r"\b(when|timeline|chronology|order of events)\b",
                r"\b(book \d+|through book|up to book|by book)\b",
                r"\b(first|second|third|fourth|fifth) book\b",
            ],
        }

        # Remove None patterns
        for category in patterns:
            patterns[category] = [p for p in patterns[category] if p]

        return patterns

    def classify_query(self, query_text: str) -> Tuple[str, float]:
        """
        Classify query into category

        Returns:
            tuple: (category, confidence)
        """
        query_lower = query_text.lower()

        # Score each category
        scores = {category: 0 for category in self.patterns.keys()}

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    scores[category] += 1

        # Get best match
        if max(scores.values()) == 0:
            return "general", 0.0

        best_category = max(scores, key=scores.get)
        confidence = scores[best_category] / len(self.patterns[best_category])

        logger.debug(f"📊 Query classified as: {best_category} (confidence: {confidence:.2f})")

        return best_category, confidence

    def get_stats(self) -> Dict:
        """Get classifier statistics"""
        return {
            "character_names": len(self.character_names),
            "magic_terms": len(self.magic_terms),
            "prophecy_terms": len(self.prophecy_terms),
            "location_terms": len(self.location_terms),
            "categories": list(self.patterns.keys()),
            "total_patterns": sum(len(p) for p in self.patterns.values()),
        }


# Example usage
if __name__ == "__main__":
    classifier = DynamicQueryClassifier()

    test_queries = ["Who is Rand al'Thor?", "What is the One Power?", "How does channeling work?", "What prophecies are there?", "When does Rand become the Dragon Reborn?"]

    print("\n" + "=" * 70)
    print("DYNAMIC QUERY CLASSIFIER TEST")
    print("=" * 70)

    stats = classifier.get_stats()
    print("\n📊 Classifier Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n🔍 Test Queries:")
    for query in test_queries:
        category, confidence = classifier.classify_query(query)
        print(f"\n   Q: {query}")
        print(f"   → {category} (confidence: {confidence:.2f})")
