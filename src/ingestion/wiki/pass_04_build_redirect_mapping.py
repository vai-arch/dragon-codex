"""
Build redirect mapping from Wheel of Time wiki redirect pages.

This script:
1. Scans all wiki .txt files in data/raw/wiki/
2. Identifies redirect pages (contain "Categories: Naming_redirects")
3. Queries the Fandom API to resolve redirect targets
4. Builds a mapping of redirect_name -> canonical_name
5. Saves to data/metadata/redirect_mapping.json

Usage:
    python build_redirect_mapping.py

Input: 
- data/raw/wiki/*.txt
Output: 
- data/metadata/redirect_mapping.json
- data/metadata/redirect_aliases_mapping.json

"""

import re
import time
from pathlib import Path
from src.utils.config import Config
from src.utils.logger import get_logger
from typing import Dict, Optional
import requests
import sys
from src.utils.util_files_functions import load_json_from_file, remove_file, save_json_to_file, find_files_in_folder,load_text_from_file
from src.utils.wiki_constants import REDIRECT_CATEGORIES, extract_categories, extract_page_name

# Fandom API configuration
FANDOM_API_URL = f"{Config().WIKI_BASE_URL}/api.php"
API_PARAMS_TEMPLATE = {
    "action": "query",
    "titles": "",
    "redirects": 1,
    "format": "json"
}

# Rate limiting
REQUEST_DELAY = 0.5  # seconds between API requests

WIKI_PATH = Config().WIKI_PATH
redirect_mapping_path = Config().FILE_REDIRECT_MAPPING
redirect_aliases_mapping_path = Config().FILE_REDIRECT_ALIASES_MAPPING

logger = get_logger(__name__)

def is_redirect_page(file_path: Path) -> bool:
    """Check if a wiki file is a redirect page (ANY type)."""
    
     # Regex to find any [[Category:Something]] tags
    categories = extract_categories(file_path, None)

    if not categories:
        # No categories at all
        return True

    # Check if any category matches your redirect categories
    return any(rtype.lower() in (cat.lower() for cat in categories) for rtype in REDIRECT_CATEGORIES)     

def query_redirect_target(page_name: str) -> Optional[str]:
    """Query Fandom API to get redirect target for a page."""
    try:
        params = API_PARAMS_TEMPLATE.copy()
        params["titles"] = page_name
        
        response = requests.get(FANDOM_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "query" in data and "redirects" in data["query"]:
            redirects = data["query"]["redirects"]
            if redirects and len(redirects) > 0:
                target = redirects[0].get("to")
                if target:
                    logger.debug(f"  Redirect: {page_name} -> {target}")
                    return target
        
        logger.warning(f"  API returned no redirect for {page_name}")
        return None
        
    except requests.RequestException as e:
        logger.error(f"  API request failed for {page_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"  Error processing API response for {page_name}: {e}")
        return None

def build_redirect_mapping(wiki_path: Path) -> Dict[str, str]:
    """Build complete redirect mapping from wiki files."""
    mapping = {}
    errors = []
    
    wiki_files = find_files_in_folder(wiki_path, ".txt", recursive=False )

    redirect_count = 0
    processed_count = 0
    
    for i, file_path in enumerate(wiki_files, 1):
        if i % 100 == 0:
            logger.info(f"Progress: {i}/{len(wiki_files)} files scanned, {redirect_count} redirects found")
        
        if not is_redirect_page(file_path):
            continue
        
        redirect_count += 1
        
        page_name = extract_page_name(file_path)
        if not page_name:
            errors.append({
                "file": file_path.name,
                "error": "Could not extract page name"
            })
            continue
        
        logger.debug(f"Processing redirect [{redirect_count}]: {page_name}")
        
        target = query_redirect_target(page_name)
        
        if target:
            mapping[page_name] = target
            processed_count += 1
        else:
            errors.append({
                "file": file_path.name,
                "page_name": page_name,
                "error": "API query failed or returned no redirect"
            })
        
        time.sleep(REQUEST_DELAY)
    
    logger.info("=" * 60)
    logger.info(f"Redirect mapping complete!")
    logger.info(f"Total files scanned: {len(wiki_files)}")
    logger.info(f"Redirect pages found: {redirect_count}")
    logger.info(f"Successfully mapped: {processed_count}")
    logger.info(f"Errors: {len(errors)}")
    logger.info("=" * 60)
    
    if errors:
        logger.warning(f"\n{len(errors)} errors occurred:")
        for error in errors[:10000]:
            logger.warning(f"  {error}")
        if len(errors) > 10000:
            logger.warning(f"  ... and {len(errors) - 10000} more errors")
    
    return dict(sorted(mapping.items()))

def invert_redirect_mapping(mapping: str):
    """Invert redirect mapping so that each canonical page lists all its redirect aliases."""
    
    inverted = {}

    # Build inverted mapping
    for redirect, canonical in mapping.items():
        inverted.setdefault(canonical, []).append(redirect)

    # Sort lists for consistency
    inverted = {k: sorted(v) for k, v in inverted.items()}

    return inverted

def main(complete_rebuild: bool = True):
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Dragon's Codex - Redirect Mapping Builder")
    logger.info("=" * 60)
    
    if(complete_rebuild):
        mapping = build_redirect_mapping(WIKI_PATH)
        save_json_to_file(mapping, redirect_mapping_path, indent=2)
    else:
        mapping = load_json_from_file(redirect_mapping_path)

    aliases = invert_redirect_mapping(mapping)
    save_json_to_file(aliases, redirect_aliases_mapping_path, indent=2)

    logger.info("✓ Redirect mapping complete!")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

    # result = is_redirect_page(
    #     Path("C:/Users/victor.diaz/Documents/_AI/dragon-codex/data/raw/wiki/Egwene_al'Vere.txt")
    # )
    # print(result)