import re
from typing import List, Optional, Set

from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file

paths = get_paths()

# Module-level cache
_alias_cache = {"temporal": None, "canonical_to_aliases": None}


def _load_aliases(force_reload: bool = False):
    """Load aliases with caching"""
    global _alias_cache

    if force_reload or _alias_cache["temporal"] is None:
        print(f"Loading alias files (force={force_reload})...")
        _alias_cache["temporal"] = load_json_from_file(paths.FILE_TEMPORAL_ALIASES)
        _alias_cache["canonical_to_aliases"] = load_json_from_file(paths.FILE_REDIRECT_ALIASES_MAPPING)

    return _alias_cache["temporal"], _alias_cache["canonical_to_aliases"]


def reload_aliases():
    """Call this after regenerating alias files"""
    _load_aliases(force_reload=True)
    print("Alias cache reloaded")


def extract_terms(query: str) -> List[str]:
    """
    Improved extractor for WoT queries:
    - Known aliases (exact match from alias_temporal keys)
    - Capitalized words (standard proper nouns)
    - Words after comma (for "al'vere, egwene")
    - Quoted phrases
    """
    candidates = set()

    alias_temporal, canonical_to_aliases = _load_aliases()

    # 1. Direct match against known aliases (case-insensitive)
    query_lower = query.lower()
    for alias in alias_temporal.keys():
        if alias.lower() in query_lower:
            candidates.add(alias)

    # 2. Capitalized words/phrases
    cap_matches = re.findall(r"[A-Z][a-z'A-Z-]*", query)
    candidates.update(cap_matches)

    # 3. Words after comma (surname-first)
    comma_matches = re.findall(r",\s*([a-z'A-Z-]+)", query)
    candidates.update(comma_matches)

    # 4. Quoted phrases
    quoted = re.findall(r'"([^"]+)"', query)
    candidates.update(quoted)

    # 5. Fallback: All multi-word sequences with known patterns (optional)

    return list(candidates)


def expand_query_safe(query: str, temporal_limit: Optional[int] = None) -> Set[str]:
    alias_temporal, canonical_to_aliases = _load_aliases()

    terms = extract_terms(query)
    expanded: Set[str] = set(terms)

    seen_canonicals = set()

    for term in terms:
        term_lower = term.lower()
        matched = False
        for key in alias_temporal:
            if alias_temporal[key].get("source") == "wiki_only":
                continue
            if key.lower() == term_lower:
                data = alias_temporal[key]
                canonical = data["canonical"]
                expanded.add(canonical)
                seen_canonicals.add(canonical)

                first_seen = data.get("first_seen_book")
                if temporal_limit is None or (first_seen is not None and first_seen <= temporal_limit):
                    expanded.add(term)
                elif data.get("is_obvious_variant", False):
                    expanded.add(term)
                matched = True
                break

        if not matched:
            for key, data in alias_temporal.items():
                if data["canonical"].lower() == term_lower:
                    canonical = data["canonical"]
                    expanded.add(canonical)
                    seen_canonicals.add(canonical)
                    if temporal_limit is None or data.get("is_obvious_variant", False) or data.get("first_seen_book") is None or data.get("first_seen_book") <= temporal_limit:
                        expanded.add(term)
                    break

    # Sibling expansion - BLOCK wiki_only non-obvious
    for canonical in seen_canonicals:
        if canonical in canonical_to_aliases:
            for sibling in canonical_to_aliases[canonical]:
                sibling_lower = sibling.lower()
                sib_data = None
                for key, data in alias_temporal.items():
                    if key.lower() == sibling_lower:
                        sib_data = data
                        break

                if not sib_data:
                    continue

                # NEW: Hard block wiki_only non-obvious
                if sib_data.get("source") == "wiki_only" and not sib_data.get("is_obvious_variant", False):
                    continue  # This stops Nuli, Tomas Trakand, etc.

                # Timed safe or obvious variant
                sib_first = sib_data.get("first_seen_book")
                if temporal_limit is None or (sib_first is not None and sib_first <= temporal_limit):
                    expanded.add(sibling)
                elif sib_data.get("is_obvious_variant", False):
                    expanded.add(sibling)

    print(f"DEBUG: Extracted terms: {terms} --> Expanded: {expanded}")

    return expanded


# Test
if __name__ == "__main__":
    # tests = ["Who is al'vere, egwene in book 3?", "Who is Aan'allein?", "What is Tel'aran'rhiod?", "Explain the Warder bond", "Who is aeldrine?"]
    tests = ["Who is Rand al'Thor?"]
    for test in tests:
        print(f"\nQuery: {test}")
        expanded = expand_query_safe(test, temporal_limit=3)
        print(f"Expanded: {expanded}")
