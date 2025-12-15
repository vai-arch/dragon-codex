"""
Dragon's Codex - Prophecy & Magic Index Builder v2.0
Builds comprehensive prophecy and magic system indexes using wiki categories.

Input:
- wiki_prophecy.json (prophecy pages with categories)
- wiki_magic.json (magic system pages with categories)

Output:
- prophecy_index.json
- magic_system_index.json

"""

import sys
import traceback
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file, save_json_to_file
from src.utils.util_statistics import total_statistics_logging
from src.utils.wiki_constants import (
    classify_magic_page,
)

# File paths
in_file_wiki_prophecies = None
in_file_wiki_magic = None
out_file_prophecy_index = None
out_file_magic_index = None


def extract_overview(sections: List[Dict]) -> str:
    """Extract overview/description from sections."""
    for section in sections:
        title = section.get("title", "").lower()
        if title in ["overview", "description"]:
            content = section.get("content", "").strip()
            if content:
                return content

    # If no overview section, try first substantial section
    for section in sections:
        title = section.get("title", "").lower()
        if title not in ["categories", "see also", "external links", "references"]:
            content = section.get("content", "").strip()
            if len(content) > 50:
                return content

    return ""


def determine_prophecy_type(page_name: str, categories: List[str]) -> str:
    """Determine prophecy type from page name and categories."""
    page_lower = page_name.lower()

    if "foretelling" in page_lower or "Foretellings" in categories:
        return "Foretelling"
    elif "viewing" in page_lower:
        return "Viewing"
    elif "prophecy" in page_lower or "Prophecies" in categories:
        return "Prophecy"

    return "Unknown"


def process_prophecy(filename: str, page_data: Dict) -> Dict:
    """Process a single prophecy page."""
    page_name = page_data.get("page_name", "")
    categories = page_data.get("metadata", {}).get("categories", [])
    sections = page_data.get("sections", [])
    aliases = page_data.get("aliases", [])

    # Build prophecy entry
    entry = {
        "page_name": page_name,
        "filename": filename,
    }

    # Add aliases if present
    if aliases:
        entry["aliases"] = aliases

    # Determine type from categories and name
    prophecy_type = determine_prophecy_type(page_name, categories)
    entry["type"] = prophecy_type

    # Extract description
    description = extract_overview(sections)
    if description:
        entry["description"] = description

    # Store categories
    if categories:
        entry["categories"] = categories

    return entry


def process_magic(filename: str, page_data: Dict) -> Dict:
    """Process a single magic page."""
    page_name = page_data.get("page_name", "")
    categories = page_data.get("metadata", {}).get("categories", [])
    sections = page_data.get("sections", [])
    aliases = page_data.get("aliases", [])

    # Build magic entry
    entry = {
        "page_name": page_name,
        "filename": filename,
    }

    # Add aliases if present
    if aliases:
        entry["aliases"] = aliases

    # Classify using categories
    magic_type = classify_magic_page(categories)
    entry["type"] = magic_type

    # More specific classification from categories
    if "Angreal" in categories:
        entry["object_type"] = "Angreal"
    elif "Sa'angreal" in categories:
        entry["object_type"] = "Sa'angreal"
    elif "Ter'angreal" in categories:
        entry["object_type"] = "Ter'angreal"

    # Check for specific magic concepts
    if "One_Power" in categories:
        entry["power_related"] = True
    if "Weaves" in categories:
        entry["is_weave"] = True
    if "Talents" in categories:
        entry["is_talent"] = True
    if "Shadowspawn" in categories:
        entry["is_shadowspawn"] = True

    # Extract description
    description = extract_overview(sections)
    if description:
        entry["description"] = description

    # Store all categories
    if categories:
        entry["categories"] = categories

    return entry


def process_all_prophecies(prophecies: Dict) -> tuple:
    """Process all prophecy pages."""
    print(f"\n🔮 Processing {len(prophecies):,} prophecy pages...")

    prophecy_index = {}
    # fmt: off
    stats = {"total_prophecies": 0, 
             "prophecies_with_aliases": 0, 
             "prophecies_with_description": 0, 
             "by_type": defaultdict(int)
             }
    # fmt: on

    for filename, page_data in prophecies.items():
        entry = process_prophecy(filename, page_data)
        page_name = entry["page_name"]

        prophecy_index[page_name] = entry

        # Update statistics
        stats["total_prophecies"] += 1
        if entry.get("aliases"):
            stats["prophecies_with_aliases"] += 1
        if entry.get("description"):
            stats["prophecies_with_description"] += 1
        stats["by_type"][entry["type"]] += 1

    print(f"   ✓ Processed {stats['total_prophecies']:,} prophecies")

    # fmt: off
    statistics = {
        "name": "prophecies",
        "metrics": stats
    }
    # fmt: on
    return prophecy_index, statistics


def process_all_magic(magic: Dict) -> tuple:
    """Process all magic pages."""
    print(f"\n✨ Processing {len(magic):,} magic pages...")

    magic_index = {}
    stats = {
        "total": 0,
        "with_aliases": 0,
        "with_description": 0,
        "by_type": defaultdict(int),
        "power_objects": 0,
        "weaves": 0,
        "talents": 0,
        "shadowspawn": 0,
    }

    for filename, page_data in magic.items():
        entry = process_magic(filename, page_data)
        page_name = entry["page_name"]

        magic_index[page_name] = entry

        # Update statistics
        stats["total"] += 1
        if entry.get("aliases"):
            stats["with_aliases"] += 1
        if entry.get("description"):
            stats["with_description"] += 1
        stats["by_type"][entry["type"]] += 1

        if entry.get("object_type"):
            stats["power_objects"] += 1
        if entry.get("is_weave"):
            stats["weaves"] += 1
        if entry.get("is_talent"):
            stats["talents"] += 1
        if entry.get("is_shadowspawn"):
            stats["shadowspawn"] += 1

    print(f"   ✓ Processed {stats['total']:,} magic pages")

    # fmt: off
    statistics = {
        "name": "magic",
        "metrics": stats
    }
    # fmt: on

    return magic_index, statistics


def validate_indexes(prophecy_index: Dict, magic_index: Dict):
    """Validate the indexes with sample checks."""
    print("\n🔍 Validating indexes...")

    # Check prophecy entries
    print("\n   Sample Prophecy Entries:")
    for i, (name, entry) in enumerate(list(prophecy_index.items())[:3]):
        print(f"      {name}:")
        print(f"         Type: {entry.get('type', 'N/A')}")
        print(f"         Aliases: {len(entry.get('aliases', []))}")
        print(f"         Has description: {bool(entry.get('description'))}")

    # Check magic entries
    print("\n   Sample Magic Entries:")
    for i, (name, entry) in enumerate(list(magic_index.items())[:3]):
        print(f"      {name}:")
        print(f"         Type: {entry.get('type', 'N/A')}")
        print(f"         Object type: {entry.get('object_type', 'N/A')}")
        print(f"         Has description: {bool(entry.get('description'))}")

    print("\n   ✅ Validation complete!")


def main():
    start_time = datetime.now()

    statistics = []

    # Step 1: Load data
    prophecies = load_json_from_file(in_file_wiki_prophecies)
    magic = load_json_from_file(in_file_wiki_magic)

    # Step 2: Process prophecies
    prophecy_index, prophecy_stats = process_all_prophecies(prophecies)
    statistics.append(prophecy_stats)

    # Step 3: Process magic
    magic_index, magic_stats = process_all_magic(magic)
    statistics.append(magic_stats)

    # Step 4: Validate
    validate_indexes(prophecy_index, magic_index)

    save_json_to_file(prophecy_index, out_file_prophecy_index, indent=2)
    save_json_to_file(magic_index, out_file_magic_index, indent=2)

    total_time = datetime.now() - start_time

    total_statistics_logging(total_time=total_time, log_name="prc_07_build_prophecy_and_magic_index", statistics=statistics, title="PROPHECY & MAGIC INDEX", tables=False)


if __name__ == "__main__":
    paths = get_paths()

    in_file_wiki_prophecies = paths.FILE_WIKI_PROPHECIES
    in_file_wiki_magic = paths.FILE_WIKI_MAGIC
    out_file_prophecy_index = paths.FILE_PROPHECY_INDEX
    out_file_magic_index = paths.FILE_MAGIC_SYSTEM_INDEX

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
