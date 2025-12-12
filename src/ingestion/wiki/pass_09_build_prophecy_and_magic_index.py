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

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional
from src.utils.util_files_functions import load_json_from_file, save_json_to_file

from src.utils.config import Config
from src.utils.wiki_constants import (
    PROPHECY_CATEGORIES,
    POWER_OBJECTS,
    ONE_POWER_CONCEPTS,
    MAGIC_PLACES,
    MAGIC_ENTITIES,
    MAGIC_WEAPONS,
    classify_magic_page,
)

config = Config()

# File paths
prophecies_file = config.FILE_WIKI_PROPHECIES
magic_file = config.FILE_WIKI_MAGIC
prophecy_output = config.FILE_PROPHECY_INDEX
magic_output = config.FILE_MAGIC_SYSTEM_INDEX

def extract_overview(sections: List[Dict]) -> str:
    """Extract overview/description from sections."""
    for section in sections:
        title = section.get('title', '').lower()
        if title in ['overview', 'description']:
            content = section.get('content', '').strip()
            if content:
                return content
    
    # If no overview section, try first substantial section
    for section in sections:
        title = section.get('title', '').lower()
        if title not in ['categories', 'see also', 'external links', 'references']:
            content = section.get('content', '').strip()
            if len(content) > 50:
                return content
    
    return ""


def determine_prophecy_type(page_name: str, categories: List[str]) -> str:
    """Determine prophecy type from page name and categories."""
    page_lower = page_name.lower()
    
    if 'foretelling' in page_lower or 'Foretellings' in categories:
        return 'Foretelling'
    elif 'viewing' in page_lower:
        return 'Viewing'
    elif 'prophecy' in page_lower or 'Prophecies' in categories:
        return 'Prophecy'
    
    return 'Unknown'


def process_prophecy(filename: str, page_data: Dict) -> Dict:
    """Process a single prophecy page."""
    page_name = page_data.get('page_name', '')
    categories = page_data.get('metadata', {}).get('categories', [])
    sections = page_data.get('sections', [])
    aliases = page_data.get('aliases', [])
    
    # Build prophecy entry
    entry = {
        'page_name': page_name,
        'filename': filename,
    }
    
    # Add aliases if present
    if aliases:
        entry['aliases'] = aliases
    
    # Determine type from categories and name
    prophecy_type = determine_prophecy_type(page_name, categories)
    entry['type'] = prophecy_type
    
    # Extract description
    description = extract_overview(sections)
    if description:
        entry['description'] = description
    
    # Store categories
    if categories:
        entry['categories'] = categories
    
    return entry


def process_magic(filename: str, page_data: Dict) -> Dict:
    """Process a single magic page."""
    page_name = page_data.get('page_name', '')
    categories = page_data.get('metadata', {}).get('categories', [])
    sections = page_data.get('sections', [])
    aliases = page_data.get('aliases', [])
    
    # Build magic entry
    entry = {
        'page_name': page_name,
        'filename': filename,
    }
    
    # Add aliases if present
    if aliases:
        entry['aliases'] = aliases
    
    # Classify using categories
    magic_type = classify_magic_page(categories)
    entry['type'] = magic_type
    
    # More specific classification from categories
    if 'Angreal' in categories:
        entry['object_type'] = 'Angreal'
    elif 'Sa\'angreal' in categories:
        entry['object_type'] = 'Sa\'angreal'
    elif 'Ter\'angreal' in categories:
        entry['object_type'] = 'Ter\'angreal'
    
    # Check for specific magic concepts
    if 'One_Power' in categories:
        entry['power_related'] = True
    if 'Weaves' in categories:
        entry['is_weave'] = True
    if 'Talents' in categories:
        entry['is_talent'] = True
    if 'Shadowspawn' in categories:
        entry['is_shadowspawn'] = True
    
    # Extract description
    description = extract_overview(sections)
    if description:
        entry['description'] = description
    
    # Store all categories
    if categories:
        entry['categories'] = categories
    
    return entry


def process_all_prophecies(prophecies: Dict) -> tuple:
    """Process all prophecy pages."""
    print(f"\n🔮 Processing {len(prophecies):,} prophecy pages...")
    
    prophecy_index = {}
    stats = {
        'total': 0,
        'with_aliases': 0,
        'with_description': 0,
        'by_type': defaultdict(int)
    }
    
    for filename, page_data in prophecies.items():
        entry = process_prophecy(filename, page_data)
        page_name = entry['page_name']
        
        prophecy_index[page_name] = entry
        
        # Update statistics
        stats['total'] += 1
        if entry.get('aliases'):
            stats['with_aliases'] += 1
        if entry.get('description'):
            stats['with_description'] += 1
        stats['by_type'][entry['type']] += 1
    
    print(f"   ✓ Processed {stats['total']:,} prophecies")
    
    return prophecy_index, stats


def process_all_magic(magic: Dict) -> tuple:
    """Process all magic pages."""
    print(f"\n✨ Processing {len(magic):,} magic pages...")
    
    magic_index = {}
    stats = {
        'total': 0,
        'with_aliases': 0,
        'with_description': 0,
        'by_type': defaultdict(int),
        'power_objects': 0,
        'weaves': 0,
        'talents': 0,
        'shadowspawn': 0
    }
    
    for filename, page_data in magic.items():
        entry = process_magic(filename, page_data)
        page_name = entry['page_name']
        
        magic_index[page_name] = entry
        
        # Update statistics
        stats['total'] += 1
        if entry.get('aliases'):
            stats['with_aliases'] += 1
        if entry.get('description'):
            stats['with_description'] += 1
        stats['by_type'][entry['type']] += 1
        
        if entry.get('object_type'):
            stats['power_objects'] += 1
        if entry.get('is_weave'):
            stats['weaves'] += 1
        if entry.get('is_talent'):
            stats['talents'] += 1
        if entry.get('is_shadowspawn'):
            stats['shadowspawn'] += 1
    
    print(f"   ✓ Processed {stats['total']:,} magic pages")
    
    return magic_index, stats


def print_statistics(prophecy_stats: Dict, magic_stats: Dict):
    """Print comprehensive statistics."""
    print(f"\n📊 Prophecy Index Statistics:")
    print(f"   Total prophecies:              {prophecy_stats['total']:5,}")
    print(f"   With aliases:                  {prophecy_stats['with_aliases']:5,}")
    print(f"   With descriptions:             {prophecy_stats['with_description']:5,}")
    print(f"\n   By Type:")
    for ptype, count in sorted(prophecy_stats['by_type'].items()):
        print(f"   {ptype:30s} {count:5,}")
    
    print(f"\n📊 Magic System Index Statistics:")
    print(f"   Total magic pages:             {magic_stats['total']:5,}")
    print(f"   With aliases:                  {magic_stats['with_aliases']:5,}")
    print(f"   With descriptions:             {magic_stats['with_description']:5,}")
    print(f"\n   By Type:")
    for mtype, count in sorted(magic_stats['by_type'].items()):
        print(f"   {mtype:30s} {count:5,}")
    print(f"\n   Special Classifications:")
    print(f"   Power objects:                 {magic_stats['power_objects']:5,}")
    print(f"   Weaves:                        {magic_stats['weaves']:5,}")
    print(f"   Talents:                       {magic_stats['talents']:5,}")
    print(f"   Shadowspawn:                   {magic_stats['shadowspawn']:5,}")


def validate_indexes(prophecy_index: Dict, magic_index: Dict):
    """Validate the indexes with sample checks."""
    print(f"\n🔍 Validating indexes...")
    
    # Check prophecy entries
    print(f"\n   Sample Prophecy Entries:")
    for i, (name, entry) in enumerate(list(prophecy_index.items())[:3]):
        print(f"      {name}:")
        print(f"         Type: {entry.get('type', 'N/A')}")
        print(f"         Aliases: {len(entry.get('aliases', []))}")
        print(f"         Has description: {bool(entry.get('description'))}")
    
    # Check magic entries
    print(f"\n   Sample Magic Entries:")
    for i, (name, entry) in enumerate(list(magic_index.items())[:3]):
        print(f"      {name}:")
        print(f"         Type: {entry.get('type', 'N/A')}")
        print(f"         Object type: {entry.get('object_type', 'N/A')}")
        print(f"         Has description: {bool(entry.get('description'))}")
    
    print(f"\n   ✅ Validation complete!")


def main():
    """Main indexing function."""
    
    print("\n" + "=" * 80)
    print("DRAGON'S CODEX - PROPHECY & MAGIC INDEX BUILDER v2.0")
    print("Category-Based Extraction")
    print("=" * 80)
    
    print(f"\n📂 Configuration:")
    print(f"   Prophecy file:    {prophecies_file}")
    print(f"   Magic file:       {magic_file}")
    print(f"   Prophecy output:  {prophecy_output}")
    print(f"   Magic output:     {magic_output}")
    
    start_time = datetime.now()
    
    # Step 1: Load data
    prophecies = load_json_from_file(prophecies_file)
    magic = load_json_from_file(magic_file)
    
    # Step 2: Process prophecies
    prophecy_index, prophecy_stats = process_all_prophecies(prophecies)
    
    # Step 3: Process magic
    magic_index, magic_stats = process_all_magic(magic)
    
    # Step 4: Print statistics
    print_statistics(prophecy_stats, magic_stats)
    
    # Step 5: Validate
    validate_indexes(prophecy_index, magic_index)
    

    save_json_to_file(prophecy_index, prophecy_output, indent=2)
    save_json_to_file(magic_index, magic_output, indent=2)  
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("PROPHECY & MAGIC INDEX BUILD COMPLETE!")
    print("=" * 80)
    print(f"\n⏱️  Total time: {duration}")
    print(f"📊 Prophecies indexed: {len(prophecy_index):,}")
    print(f"📊 Magic pages indexed: {len(magic_index):,}")
    print(f"\n✅ Week 3 Goal 4: COMPLETE (v2.0)!\n")


if __name__ == "__main__":
    main()