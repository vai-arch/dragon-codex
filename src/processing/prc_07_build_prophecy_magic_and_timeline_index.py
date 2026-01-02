"""
Dragon's Codex - Prophecy, Magic & Timeline Index Builder v3.0
Builds comprehensive indexes for prophecy, magic system, and timeline entries.

Input:
- wiki_prophecy.json
- wiki_magic.json
- wiki_timeline.json (new)

Output:
- prophecy_index.json
- magic_system_index.json
- timeline_index.json

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
    MAGIC_ENTITIES,
    MAGIC_PLACES,
    MAGIC_WEAPONS,
    ONE_POWER_CONCEPTS,
    POWER_OBJECTS,
)

# File paths
in_file_wiki_prophecies = None
in_file_wiki_magic = None
in_file_wiki_timeline = None
out_file_prophecy_index = None
out_file_magic_index = None
out_file_timeline_index = None


def extract_overview(sections: List[Dict]) -> str:
    """Extract overview/description from sections."""
    for section in sections:
        title = section.get("title", "").lower()
        if title in ["overview", "description", "events"]:
            content = section.get("content", "").strip()
            if content:
                return content

    # Fallback: first substantial section
    for section in sections:
        title = section.get("title", "").lower()
        if title not in ["categories", "see also", "external links", "references"]:
            content = section.get("content", "").strip()
            if len(content) > 30:
                return content

    return ""


def determine_prophecy_type(page_name: str, categories: List[str]) -> str:
    page_lower = page_name.lower()
    if "foretelling" in page_lower or "Foretellings" in categories:
        return "Foretelling"
    elif "viewing" in page_lower:
        return "Viewing"
    elif "prophecy" in page_lower or "Prophecies" in categories:
        return "Prophecy"
    return "Unknown"


def process_prophecy(filename: str, page_data: Dict) -> Dict:
    page_name = page_data.get("page_name", "")
    categories = page_data.get("metadata", {}).get("categories", [])
    sections = page_data.get("sections", [])
    aliases = page_data.get("aliases", [])

    entry = {
        "page_name": page_name,
        "filename": filename,
        "type": determine_prophecy_type(page_name, categories),
    }

    if aliases:
        entry["aliases"] = aliases
    description = extract_overview(sections)
    if description:
        entry["description"] = description
    if categories:
        entry["categories"] = categories

    return entry


def classify_magic_page(categories: List[str]) -> str:
    for category in categories:
        if category in POWER_OBJECTS:
            return "power_object"
        if category in ONE_POWER_CONCEPTS:
            return "concept"
        if category in MAGIC_PLACES:
            return "place"
        if category in MAGIC_ENTITIES:
            return "entity"
        if category in MAGIC_WEAPONS:
            return "weapon"
    return "other"


def process_magic(filename: str, page_data: Dict) -> Dict:
    page_name = page_data.get("page_name", "")
    categories = page_data.get("metadata", {}).get("categories", [])
    sections = page_data.get("sections", [])
    aliases = page_data.get("aliases", [])

    entry = {
        "page_name": page_name,
        "filename": filename,
        "type": classify_magic_page(categories),
    }

    if aliases:
        entry["aliases"] = aliases

    # Specific object types
    if any(c in categories for c in ["Angreal", "Sa'angreal", "Ter'angreal"]):
        entry["object_type"] = next(c for c in ["Angreal", "Sa'angreal", "Ter'angreal"] if c in categories)

    # Flags
    if "One_Power" in categories:
        entry["power_related"] = True
    if "Weaves" in categories:
        entry["is_weave"] = True
    if "Talents" in categories:
        entry["is_talent"] = True
    if "Shadowspawn" in categories:
        entry["is_shadowspawn"] = True

    description = extract_overview(sections)
    if description:
        entry["description"] = description
    if categories:
        entry["categories"] = categories

    return entry


def determine_timeline_type(page_name: str, page_type: str, categories: List[str]) -> str:
    """Determine timeline entry type."""
    page_lower = page_name.lower()
    page_type_lower = page_type.lower()

    if "battle" in page_lower or "Battles" in categories:
        return "battle"
    if "war" in page_lower or "Wars" in categories:
        return "war"
    if page_type_lower == "historical":
        return "date_year"
    if any(age in page_lower for age in ["age", "era"]):
        return "era"
    if "NE" in page_name or any(cat in categories for cat in ["New_Era_chronology", "Time", "Dates"]):
        return "date_year"

    return "event"


def process_timeline(filename: str, page_data: Dict) -> Dict:
    """Process a single timeline page."""
    page_name = page_data.get("page_name", "")
    page_type = page_data.get("type", "historical")
    categories = page_data.get("metadata", {}).get("categories", [])
    sections = page_data.get("sections", [])
    aliases = page_data.get("aliases", [])

    entry = {
        "page_name": page_name,
        "filename": filename,
        "type": determine_timeline_type(page_name, page_type, categories),
    }

    if aliases:
        entry["aliases"] = aliases

    description = extract_overview(sections)
    if description:
        entry["description"] = description

    if categories:
        entry["categories"] = categories

    # Extract events if present
    events = []
    for section in sections:
        if section.get("title", "").lower() == "events":
            events.append(section.get("content", "").strip())
    if events:
        entry["events"] = events

    return entry


def process_all_prophecies(prophecies: Dict) -> tuple:
    print(f"\nProcessing {len(prophecies):,} prophecy pages...")
    index = {}
    stats = {"total_prophecies": 0, "prophecies_with_aliases": 0, "prophecies_with_description": 0, "by_type": defaultdict(int)}

    for filename, page_data in prophecies.items():
        entry = process_prophecy(filename, page_data)
        index[entry["page_name"]] = entry
        stats["total_prophecies"] += 1
        if entry.get("aliases"):
            stats["prophecies_with_aliases"] += 1
        if entry.get("description"):
            stats["prophecies_with_description"] += 1
        stats["by_type"][entry["type"]] += 1

    print(f"   Processed {stats['total_prophecies']:,} prophecies")
    return index, {"name": "prophecies", "metrics": stats}


def process_all_magic(magic: Dict) -> tuple:
    print(f"\nProcessing {len(magic):,} magic pages...")
    index = {}
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
        index[entry["page_name"]] = entry
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

    print(f"   Processed {stats['total']:,} magic pages")
    return index, {"name": "magic", "metrics": stats}


def process_all_timeline(timeline: Dict) -> tuple:
    print(f"\nProcessing {len(timeline):,} timeline pages...")
    index = {}
    stats = {
        "total": 0,
        "with_aliases": 0,
        "with_description": 0,
        "with_events": 0,
        "by_type": defaultdict(int),
    }

    for filename, page_data in timeline.items():
        entry = process_timeline(filename, page_data)
        index[entry["page_name"]] = entry
        stats["total"] += 1
        if entry.get("aliases"):
            stats["with_aliases"] += 1
        if entry.get("description"):
            stats["with_description"] += 1
        if entry.get("events"):
            stats["with_events"] += 1
        stats["by_type"][entry["type"]] += 1

    print(f"   Processed {stats['total']:,} timeline entries")
    return index, {"name": "timeline", "metrics": stats}


def validate_indexes(prophecy_index: Dict, magic_index: Dict, timeline_index: Dict):
    print("\nValidating indexes...")

    print("\n   Sample Prophecy Entries:")
    for name, entry in list(prophecy_index.items())[:3]:
        print(f"      {name}: Type={entry.get('type')}, Desc={'Yes' if entry.get('description') else 'No'}")

    print("\n   Sample Magic Entries:")
    for name, entry in list(magic_index.items())[:3]:
        print(f"      {name}: Type={entry.get('type')}, Object={entry.get('object_type', 'N/A')}")

    print("\n   Sample Timeline Entries:")
    for name, entry in list(timeline_index.items())[:3]:
        print(f"      {name}: Type={entry.get('type')}, Events={'Yes' if entry.get('events') else 'No'}")

    print("\n   Validation complete!")


def main():
    start_time = datetime.now()
    statistics = []

    # Load data
    prophecies = load_json_from_file(in_file_wiki_prophecies)
    magic = load_json_from_file(in_file_wiki_magic)
    timeline = load_json_from_file(in_file_wiki_timeline)

    # Process each
    prophecy_index, prophecy_stats = process_all_prophecies(prophecies)
    magic_index, magic_stats = process_all_magic(magic)
    timeline_index, timeline_stats = process_all_timeline(timeline)

    statistics.extend([prophecy_stats, magic_stats, timeline_stats])

    # Validate
    validate_indexes(prophecy_index, magic_index, timeline_index)

    # Save
    save_json_to_file(prophecy_index, out_file_prophecy_index, indent=2)
    save_json_to_file(magic_index, out_file_magic_index, indent=2)
    save_json_to_file(timeline_index, out_file_timeline_index, indent=2)

    total_time = datetime.now() - start_time
    total_statistics_logging(
        total_time=total_time,
        log_name="prc_08_build_prophecy_magic_timeline_index",
        statistics=statistics,
        title="PROPHECY, MAGIC & TIMELINE INDEX",
        tables=False,
    )


if __name__ == "__main__":
    paths = get_paths()

    in_file_wiki_prophecies = paths.FILE_WIKI_PROPHECIES
    in_file_wiki_magic = paths.FILE_WIKI_MAGIC
    in_file_wiki_timeline = paths.FILE_WIKI_TIMELINE

    out_file_prophecy_index = paths.FILE_PROPHECY_INDEX
    out_file_magic_index = paths.FILE_MAGIC_SYSTEM_INDEX
    out_file_timeline_index = paths.FILE_TIMELINE_INDEX

    try:
        main()
        exit_code = 0
    except Exception as e:
        print("An error occurred in the script:", str(e))
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)
