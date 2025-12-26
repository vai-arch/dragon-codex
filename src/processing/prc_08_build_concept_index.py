"""
Build concept_index.json from wiki_concept.json
Classifies concepts into taxonomy categories (locations, creatures, items, etc.)
Excludes character-related and meta wiki categories

USAGE:
  This script should be run from the actual project directory, not the container.
  Copy to: src/ingestion/wiki/pass_16_build_concept_index.py
  Then run: python src/ingestion/wiki/pass_16_build_concept_index.py
"""

import sys
import traceback
from datetime import datetime

from tqdm import tqdm

from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file, save_json_to_file
from src.utils.util_statistics import total_statistics_logging
from src.utils.wiki_constants import (
    CONCEPT_CATEGORIES,
    CREATURE_CATEGORIES,
    CULTURAL_CATEGORIES,
    HISTORICAL_CATEGORIES,
    ITEM_CATEGORIES,
    LOCATION_CATEGORIES,
    ORGANIZATION_CATEGORIES,
)

in_file_wiki_concept = None
in_file_filename_to_categories = None
out_file_concept_index = None

TAXONOMY = {
    "LOCATION": LOCATION_CATEGORIES,
    "CREATURE": CREATURE_CATEGORIES,
    "ITEM": ITEM_CATEGORIES,
    "HISTORICAL": HISTORICAL_CATEGORIES,
    "CULTURAL": CULTURAL_CATEGORIES,
    "CONCEPT": CONCEPT_CATEGORIES,
    "ORGANIZATION": ORGANIZATION_CATEGORIES,
}


def classify_concept(categories, taxonomy):
    """
    Classify a concept based on its wiki categories
    Returns (category_type, matching_categories) or (None, []) if excluded/unclassified
    """
    if not categories:
        return None, []

    # Then classify into taxonomy groups
    # Track all matching categories for this concept
    location_matches = []
    creature_matches = []
    item_matches = []
    historical_matches = []
    cultural_matches = []
    organization_matches = []
    concept_matches = []

    for cat in categories:
        # Check each taxonomy group
        for keyword in taxonomy["LOCATION"]:
            if keyword in cat:
                location_matches.append(cat)
                break

        for keyword in taxonomy["CREATURE"]:
            if keyword in cat:
                creature_matches.append(cat)
                break

        for keyword in taxonomy["ITEM"]:
            if keyword in cat:
                item_matches.append(cat)
                break

        for keyword in taxonomy["ORGANIZATION"]:
            if keyword in cat:
                organization_matches.append(cat)
                break

        for keyword in taxonomy["HISTORICAL"]:
            if keyword in cat:
                historical_matches.append(cat)
                break

        for keyword in taxonomy["CULTURAL"]:
            if keyword in cat:
                cultural_matches.append(cat)
                break

        for keyword in taxonomy["CONCEPT"]:
            if keyword in cat:
                concept_matches.append(cat)
                break

    # Prioritize classification (locations > creatures > items > historical > cultural > concept)
    if location_matches:
        return "location", location_matches
    elif creature_matches:
        return "creature", creature_matches
    elif organization_matches:
        return "organization", creature_matches
    elif item_matches:
        return "item", item_matches
    elif historical_matches:
        return "historical", historical_matches
    elif cultural_matches:
        return "cultural", cultural_matches
    elif concept_matches:
        return "concept", concept_matches

    # Unclassified
    return None, []


def build_concept_index(wiki_concepts, category_mappings, taxonomy):
    """Build the concept index with taxonomy classification"""

    concepts = []
    excluded_count = 0
    unclassified_count = 0
    uncategorized_count = 0

    stats_concept_types = {
        "location": 0,
        "creature": 0,
        "item": 0,
        "historical": 0,
        "organization": 0,
        "cultural": 0,
        "concept": 0,
    }

    print("\nProcessing concepts...")

    for page in tqdm(wiki_concepts, desc="Processing wiki concepts"):
        filename = page.get("filename", "")
        name = page.get("page_name", "")

        # Get categories for this file
        categories = category_mappings.get(filename, [])

        UNWANTED_CATEGORIES = {"Short_pages", "Citation_needed"}
        categories = [c for c in categories if c not in UNWANTED_CATEGORIES]

        # Classify
        concept_type, matching_categories = classify_concept(categories, taxonomy)

        if concept_type is None:
            if len(categories) == 0:
                uncategorized_count += 1
                continue
            if matching_categories == []:  # Excluded
                excluded_count += 1
                print(f"Excluded: --{filename}------{categories}")
            else:  # Unclassified
                unclassified_count += 1
            continue

        # Create concept entry
        concept_entry = {
            "name": name,
            "type": concept_type,
            "filename": filename,
            "categories": matching_categories,
            "all_wiki_categories": categories,
        }

        # Add overview if present in sections
        for section in page.get("sections", []):
            if section.get("title") == "Overview":
                concept_entry["overview"] = section.get("content", "")
                break

        # Add aliases if present
        if page.get("aliases"):
            concept_entry["aliases"] = page["aliases"]

        concepts.append(concept_entry)
        stats_concept_types[concept_type] += 1

    # fmt: off
    statistics = {
        "name": "concept_statistics",
        "metrics": {
            "total_concepts": len(concepts),
            "excluded_count": excluded_count,
            "unclassified_count": unclassified_count,
            "uncategorized_count": uncategorized_count,
            "concept_types": stats_concept_types
        }
    }
    # fmt: on
    return concepts, statistics, stats_concept_types


def main():
    start_time = datetime.now()

    # Load data
    wiki_concepts_dict = load_json_from_file(in_file_wiki_concept)
    wiki_concepts = list(wiki_concepts_dict.values())

    category_mappings = load_json_from_file(in_file_filename_to_categories)

    # Build index
    concepts, statistics, concept_types = build_concept_index(wiki_concepts, category_mappings, TAXONOMY)

    # Save
    concepts_dict = {}
    for concept in concepts:
        concept_name = concept["name"]
        concepts_dict[concept_name] = concept

    save_json_to_file(concepts_dict, out_file_concept_index, indent=2)

    total_time = datetime.now() - start_time

    total_statistics_logging(total_time=total_time, log_name="prc_08_build_concept_index", statistics=statistics, title="CONCEPTS INDEX", tables=False)


if __name__ == "__main__":
    paths = get_paths()

    in_file_wiki_concept = paths.FILE_WIKI_CONCEPT
    in_file_filename_to_categories = paths.FILE_FILENAME_TO_CATEGORIES
    out_file_concept_index = paths.FILE_CONCEPT_INDEX

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
