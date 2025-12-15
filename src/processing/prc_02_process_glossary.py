"""
Build glossary-to-wiki filename mapping.

This script:
1. Loads unified glossary JSON (all terms from all books)
2. Tries various filename transformation strategies
3. Checks if corresponding wiki .txt file exists
4. Creates mapping: glossary_term -> wiki_filename (or null)
5. Reports statistics and unmatched terms

This is just for review purposes, the glossary_to_wiki_mapping.json is going to be used directly
The 32 unmatched terms will be handled in the next step by creating minimal wiki stubs for them.

THERE ARE 32 Terms Uunmatched (93.6%)
        Al Ellisande\!
        Carai an Caldazar\!
        Carai an Ellisande\!
        Covenant of the Ten Nations
        Great Pattern
        Bittern
        Do Miere A’vron
        Great Game, the
        Hide
        Kith
        Leashed Ones
        Sung Wood
        Tai’shar
        Tia mi aven Moridin isainde vadin
        Tree, the
        Treesong
        Fetches
        Treekillers
        Armsmen
        Companions, the
        Der’morat
        Lance-Captain
        Master of the Lances
        Sea Folk hierarchy
        Sword-Captain
        Depository
        Lady of the Shadows
        Stump
        Forced
        Standardbearer
        Succession
        Head of the Great Council of Thirteen

Usage:
    python build_glossary_wiki_mapping.py
"""

import sys
import traceback
from datetime import datetime
from typing import Dict, Optional, Set

from tqdm import tqdm

from src.utils.logger import get_logger
from src.utils.paths import get_paths
from src.utils.util_files_functions import find_files_in_folder, load_json_from_file, save_json_to_file
from src.utils.util_statistics import total_statistics_logging

cfg_wiki_path = None
in_file_unified_glossay = None
out_file_glossary_wiki_mapping = None

logger = get_logger(__name__)


def try_transformations(term: str, wiki_files: Set[str]) -> Optional[str]:
    """
    Try various filename transformations to find matching wiki file.

    Returns:
        Wiki filename if found, None otherwise
    """

    # ========== ADD THIS FIRST (NORMALIZE APOSTROPHES) ==========
    # Normalize curly/smart apostrophes to straight apostrophes
    # Glossary has ' (U+2019) but filenames have ' (U+0027)
    term = term.replace("\u2019", "'")
    term = term.replace("\u2018", "'")
    term = term.replace("\u2019", "'")
    term = term.replace("’", "'")
    # ===========================================================

    # Examples: "Colavaere of House Saighan" → "Colavaere.txt"
    if " of House " in term:
        first_word = term.split()[0]  # Get just the first word
        candidate = f"{first_word}.txt"
        if candidate in wiki_files:
            return candidate

    # Special case: "Term, the" → "The_Term.txt"
    if term.endswith(", the"):
        base_term = term[:-5].strip()  # Remove ", the"
        candidate = f"The_{base_term.replace(' ', '_')}.txt"
        if candidate in wiki_files:
            return candidate
        candidate = f"{base_term.replace(' ', '_')}.txt"
        if candidate in wiki_files:
            return candidate

    # Special case: "Title, The" → "The_Title.txt" (capital T)
    if term.endswith(", The"):
        base_term = term[:-5].strip()  # Remove ", The"
        candidate = f"The_{base_term.replace(' ', '_')}.txt"
        if candidate in wiki_files:
            return candidate

    # Special case: "Title, A" → "A_Title.txt"
    if term.endswith(", A"):
        base_term = term[:-3].strip()  # Remove ", A"
        candidate = f"A_{base_term.replace(' ', '_')}.txt"
        if candidate in wiki_files:
            return candidate

    # Strategy 1: Terms with comma (Lastname, Firstname format)
    if "," in term:
        # Example: "Adan, Heran" → "heran_adan.txt"
        parts = term.split(",", 1)
        if len(parts) == 2:
            lastname = parts[0].strip()
            firstname = parts[1].strip()

            # Try 1: Direct swap with original capitalization
            candidate = f"{firstname}_{lastname}.txt".replace(" ", "_")
            if candidate in wiki_files:
                return candidate

            # Try 2: Capitalize first letter of second part (for "the" → "The")
            if firstname and firstname[0].islower():
                second_part_cap = firstname[0].upper() + firstname[1:]
                candidate = f"{second_part_cap}_{lastname}.txt".replace(" ", "_")
                if candidate in wiki_files:
                    return candidate

            # Try 3: Just use first part (ignore title/descriptor after comma)
            # Handles: "Nisura, Lady" → "Nisura.txt"
            candidate = f"{lastname}.txt".replace(" ", "_")
            if candidate in wiki_files:
                return candidate
            # ===========================================

            # Try: firstname_lastname.txt (lowercase)
            candidate = f"{firstname.lower()}_{lastname.lower()}.txt"
            if candidate in wiki_files:
                return candidate

            # Try: Firstname_Lastname.txt (title case)
            candidate = f"{firstname}_{lastname}.txt"
            if candidate in wiki_files:
                return candidate

            # Special case: "Lastname, Title Firstname" → "Firstname_Lastname.txt"
            # Example: "Damodred, Lord Galadedrid" → "Galadedrid_Damodred.txt"
            firstname_words = firstname.split()
            if len(firstname_words) > 1:
                # Assume last word is the actual first name, rest are titles
                actual_firstname = firstname_words[-1]
                candidate = f"{actual_firstname}_{lastname}.txt"
                if candidate in wiki_files:
                    return candidate
    # Strategy 2: Regular terms (no comma)
    else:
        # Remove trailing ", the" if present
        cleaned = term

        # Try: Term_With_Spaces.txt (keep capitalization)
        candidate = cleaned.replace(" ", "_") + ".txt"
        if candidate in wiki_files:
            return candidate

        # Try: term_with_spaces.txt (lowercase)
        candidate = cleaned.lower().replace(" ", "_") + ".txt"
        if candidate in wiki_files:
            return candidate

        # Try: Term_With_Spaces.txt (title case each word)
        candidate = "_".join(word.capitalize() for word in cleaned.split()) + ".txt"
        if candidate in wiki_files:
            return candidate

    # Strategy 3: Exact match (just add .txt)
    candidate = term + ".txt"
    if candidate in wiki_files:
        return candidate

    # Strategy 4: Direct underscore replacement
    candidate = term.replace(" ", "_") + ".txt"
    if candidate in wiki_files:
        return candidate

    wiki_lower_map = {f.lower(): f for f in wiki_files}

    # Strategy 5: Lowercase, direct underscore replacement
    candidate = term.lower().replace(" ", "_") + ".txt"
    if candidate in wiki_lower_map:
        return wiki_lower_map[candidate]

    # Strategy 6: Title, direct underscore replacement
    candidate = term.title().replace(" ", "_") + ".txt"
    if candidate in wiki_files:
        return candidate

    return None


def build_mapping(glossary: Dict, wiki_files: Set[str]) -> Dict[str, Optional[str]]:
    """
    Build mapping from glossary terms to wiki filenames.

    Returns:
        Dictionary: {term: wiki_filename or None}
    """
    mapping = {}
    matched_count = 0

    total = len(glossary)
    logger.info(f"Processing {total} glossary terms...")

    for term, data in tqdm(glossary.items(), total=total, desc="Glossary terms"):
        # Try to find matching wiki file
        wiki_file = try_transformations(term, wiki_files)

        if wiki_file:
            mapping[term] = wiki_file
            matched_count += 1
            logger.debug(f"✓ Matched: {term} → {wiki_file}")
        else:
            mapping[term] = None
            logger.debug(f"✗ No match: {term}")

    logger.info(f"Matching complete: {matched_count}/{total} matched")

    matched = sum(1 for v in mapping.values() if v is not None)
    # fmt: off
    statistics = {
        "name": "glossary to wiki terms",
        "metrics": {
            "total" : len(mapping),
            "matched": matched,
            "unmatched": total - matched,
            "match_rate" : (matched / total * 100) if total > 0 else 0
        }
    }
    # fmt: on
    return dict(sorted(mapping.items())), statistics


def print_unmatched(mapping: Dict[str, Optional[str]], max_display: int = 50):
    """Print list of unmatched terms."""
    unmatched = [term for term, wiki_file in mapping.items() if wiki_file is None]

    if not unmatched:
        print("\n✓ All terms matched!")
        logger.info("All terms matched!")
        return

    print(f"\nUNMATCHED TERMS ({len(unmatched)} total):")
    print("-" * 60)

    for i, term in enumerate(unmatched[:max_display], 1):
        print(f"{i:3d}. {term}")

    if len(unmatched) > max_display:
        print(f"... and {len(unmatched) - max_display} more")

    print("-" * 60)

    # Log all unmatched to file
    logger.info(f"\nAll {len(unmatched)} unmatched terms:")
    for term in unmatched:
        logger.info(f"  - {term}")


def main():
    start_time = datetime.now()

    # Load data
    glossary = load_json_from_file(in_file_unified_glossay)
    wiki_filepaths = find_files_in_folder(cfg_wiki_path, ".txt")
    wiki_filenames = [p.name for p in wiki_filepaths]

    # Build mapping
    mapping, statistics = build_mapping(glossary, wiki_filenames)

    print_unmatched(mapping, max_display=50)

    # Save mapping
    save_json_to_file(mapping, out_file_glossary_wiki_mapping)

    total_time = (datetime.now() - start_time).total_seconds()

    # Print reports
    total_statistics_logging(statistics=statistics, log_name="prc_02_process_glossary", title="GLOSSARY TO WIKI", total_time=total_time)


if __name__ == "__main__":
    paths = get_paths()

    in_file_unified_glossay = paths.FILE_UNIFIED_GLOSSARY
    out_file_glossary_wiki_mapping = paths.FILE_GLOSSARY_WIKI_MAPPING
    cfg_wiki_path = paths.WIKI_PATH

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
