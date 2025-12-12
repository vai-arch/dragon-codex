"""
Build concept_index.json from wiki_concept.json
Classifies concepts into taxonomy categories (locations, creatures, items, etc.)
Excludes character-related and meta wiki categories

USAGE:
  This script should be run from the actual project directory, not the container.
  Copy to: src/ingestion/wiki/pass_16_build_concept_index.py
  Then run: python src/ingestion/wiki/pass_16_build_concept_index.py
"""

import json
import sys
from pathlib import Path

from src.utils.config import Config
from src.utils.util_files_functions import load_json_from_file, save_json_to_file
from src.utils.wiki_constants import (
    LOCATION_CATEGORIES,
    CREATURE_CATEGORIES,
    ITEM_CATEGORIES,
    HISTORICAL_CATEGORIES,
    CULTURAL_CATEGORIES,
    CONCEPT_CATEGORIES,
    ORGANIZATION_CATEGORIES,
    EXCLUDE_CATEGORIES,
)


def define_taxonomy():
    """Define concept taxonomy - which categories belong to which groups"""
    
    return {
        'LOCATION': LOCATION_CATEGORIES,
        'CREATURE': CREATURE_CATEGORIES,
        'ITEM': ITEM_CATEGORIES,
        'HISTORICAL': HISTORICAL_CATEGORIES,
        'CULTURAL': CULTURAL_CATEGORIES,
        'CONCEPT': CONCEPT_CATEGORIES,
        'ORGANIZATION': ORGANIZATION_CATEGORIES,
        'EXCLUDE': EXCLUDE_CATEGORIES,
    }


def classify_concept(categories, taxonomy):
    """
    Classify a concept based on its wiki categories
    Returns (category_type, matching_categories) or (None, []) if excluded/unclassified
    """
    if not categories:
        return None, []
    
    # First check if should be excluded
    for cat in categories:
        cat_lower = cat.lower()
        for exclude_keyword in taxonomy['EXCLUDE']:
            if exclude_keyword in cat_lower:
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
        for keyword in taxonomy['LOCATION']:
            if keyword in cat:
                location_matches.append(cat)
                break
        
        for keyword in taxonomy['CREATURE']:
            if keyword in cat:
                creature_matches.append(cat)
                break
        
        for keyword in taxonomy['ITEM']:
            if keyword in cat:
                item_matches.append(cat)
                break
        
        for keyword in taxonomy['ORGANIZATION']:
            if keyword in cat:
                organization_matches.append(cat)
                break
        
        for keyword in taxonomy['HISTORICAL']:
            if keyword in cat:
                historical_matches.append(cat)
                break
        
        for keyword in taxonomy['CULTURAL']:
            if keyword in cat:
                cultural_matches.append(cat)
                break
        
        for keyword in taxonomy['CONCEPT']:
            if keyword in cat:
                concept_matches.append(cat)
                break
    
    # Prioritize classification (locations > creatures > items > historical > cultural > concept)
    if location_matches:
        return 'location', location_matches
    elif creature_matches:
        return 'creature', creature_matches
    elif organization_matches:
        return 'organization', creature_matches
    elif item_matches:
        return 'item', item_matches
    elif historical_matches:
        return 'historical', historical_matches
    elif cultural_matches:
        return 'cultural', cultural_matches
    elif concept_matches:
        return 'concept', concept_matches
    
    # Unclassified
    return None, []


def build_concept_index(wiki_concepts, category_mappings, taxonomy):
    """Build the concept index with taxonomy classification"""
    
    concepts = []
    excluded_count = 0
    unclassified_count = 0
    
    stats = {
        'location': 0,
        'creature': 0,
        'item': 0,
        'historical': 0,
        'organization': 0,
        'cultural': 0,
        'concept': 0,
    }
    
    print("\nProcessing concepts...")
    
    for page in wiki_concepts:
        filename = page.get('filename', '')
        name = page.get('page_name', '')
        
        # Get categories for this file
        categories = category_mappings.get(filename, [])
        
        # Classify
        concept_type, matching_categories = classify_concept(categories, taxonomy)
        
        if concept_type is None:
            if matching_categories == []:  # Excluded
                excluded_count += 1
            else:  # Unclassified
                unclassified_count += 1
            continue
        
        # Create concept entry
        concept_entry = {
            'name': name,
            'type': concept_type,
            'filename': filename,
            'categories': matching_categories,
            'all_wiki_categories': categories,
        }
        
        # Add overview if present in sections
        for section in page.get('sections', []):
            if section.get('title') == 'Overview':
                concept_entry['overview'] = section.get('content', '')
                break
        
        # Add aliases if present
        if page.get('aliases'):
            concept_entry['aliases'] = page['aliases']

        concepts.append(concept_entry)
        stats[concept_type] += 1
    
    return concepts, stats, excluded_count, unclassified_count


def save_concept_index(concepts, stats, excluded_count, unclassified_count):
    """Save concept index to file"""
    
    # Create output structure - dict with name as key (like magic_index)
    concepts_dict = {}
    for concept in concepts:
        concept_name = concept['name']
        concepts_dict[concept_name] = concept
    
    # Save to file
    output_file = Config().FILE_CONCEPT_INDEX
    
    save_json_to_file(concepts_dict, output_file, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"✓ Concept index saved: {output_file}")
    print(f"{'=' * 60}")
    
    # Print statistics
    print("\nCONCEPT INDEX STATISTICS:")
    print(f"  Total concepts: {len(concepts)}")
    print(f"  Excluded (character/meta): {excluded_count}")
    print(f"  Unclassified: {unclassified_count}")
    print(f"\nBy Type:")
    for concept_type, count in sorted(stats.items()):
        print(f"  {concept_type.capitalize()}: {count}")
    
    return output_file


def main():
    """Main execution"""
    print("=" * 60)
    print("BUILDING CONCEPT INDEX")
    print("=" * 60)
    
    # Load data
    wiki_concepts_dict = load_json_from_file(Config().FILE_WIKI_CONCEPT)
    wiki_concepts = list(wiki_concepts_dict.values())
    category_mappings = load_json_from_file(Config().FILE_FILENAME_TO_CATEGORIES) 
   
    # Define taxonomy
    taxonomy = define_taxonomy()
    print(f"\n✓ Taxonomy defined with {len(taxonomy)} groups")
    
    # Build index
    concepts, stats, excluded_count, unclassified_count = build_concept_index(
        wiki_concepts, category_mappings, taxonomy
    )
    
    # Save
    save_concept_index(concepts, stats, excluded_count, unclassified_count)
    
    print("\n✓ Concept index build complete!")


if __name__ == "__main__":
    main()