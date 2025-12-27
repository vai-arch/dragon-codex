import re
from typing import List, Optional, Set

from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file

paths = get_paths()

alias_temporal = load_json_from_file(paths.FILE_TEMPORAL_ALIASES)
canonical_to_aliases = load_json_from_file(paths.FILE_REDIRECT_ALIASES_MAPPING)


def extract_terms(query: str) -> List[str]:
    """
    Improved extractor for WoT queries:
    - Known aliases (exact match from alias_temporal keys)
    - Capitalized words (standard proper nouns)
    - Words after comma (for "al'vere, egwene")
    - Quoted phrases
    """
    candidates = set()

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
    terms = extract_terms(query)
    expanded: Set[str] = set(terms)

    print(f"DEBUG: Extracted terms: {terms}")

    seen_canonicals = set()

    for term in terms:
        # Case-insensitive lookup
        term_lower = term.lower()
        matched = False
        for key in alias_temporal:
            if key.lower() == term_lower:
                data = alias_temporal[key]
                canonical = data["canonical"]
                expanded.add(canonical)
                seen_canonicals.add(canonical)

                # Add the matched term if safe
                first_seen = data.get("first_seen_book")
                if temporal_limit is None or (first_seen is not None and first_seen <= temporal_limit):
                    expanded.add(term)
                elif data.get("is_obvious_variant", False):
                    expanded.add(term)
                matched = True
                break
        if not matched:
            # If not found as alias, check if term is canonical
            for key, data in alias_temporal.items():
                if data["canonical"].lower() == term_lower:
                    canonical = data["canonical"]
                    expanded.add(canonical)
                    seen_canonicals.add(canonical)
                    # Add term if safe
                    if temporal_limit is None or data.get("first_seen_book", float("inf")) <= temporal_limit:
                        expanded.add(term)
                    break

    # Sibling expansion - case-insensitive
    for canonical in seen_canonicals:
        if canonical in canonical_to_aliases:
            for sibling in canonical_to_aliases[canonical]:
                # Case-insensitive sibling lookup
                sibling_lower = sibling.lower()
                sib_data = None
                for key, data in alias_temporal.items():
                    if key.lower() == sibling_lower:
                        sib_data = data
                        break
                if sib_data:
                    sib_first = sib_data.get("first_seen_book")
                    if temporal_limit is None or (sib_first is not None and sib_first <= temporal_limit):
                        expanded.add(sibling)
                    elif sib_data.get("is_obvious_variant", False):
                        expanded.add(sibling)

    return expanded


# Test
if __name__ == "__main__":
    tests = ["Who is al'vere, egwene in book 3?", "Who is Aan'allein?", "What is Tel'aran'rhiod?", "Explain the Warder bond", "Who is aeldrine?"]

    for test in tests:
        print(f"\nQuery: {test}")
        expanded = expand_query_safe(test, temporal_limit=3)
        print(f"Expanded: {expanded}")
