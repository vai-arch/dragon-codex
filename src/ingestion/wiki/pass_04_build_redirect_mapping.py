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
"""

import json
import re
import time
from pathlib import Path
from src.utils.config import Config
from src.utils.logger import get_logger
from typing import Dict, Optional
import requests
import sys
import logging

# Fandom API configuration
FANDOM_API_URL = "https://wot.fandom.com/api.php"
API_PARAMS_TEMPLATE = {
    "action": "query",
    "titles": "",
    "redirects": 1,
    "format": "json"
}

# Rate limiting
REQUEST_DELAY = 0.5  # seconds between API requests

# Paths (adjust if needed)
PROJECT_ROOT = Path(__file__).parent
DATA_ROOT = Config().DATA_PATH
WIKI_PATH = Config().WIKI_PATH
METADATA_PATH = Config().METADATA_PATH

# Setup logging
METADATA_PATH.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def is_redirect_page(file_path: Path) -> bool:
    """Check if a wiki file is a redirect page (ANY type)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for any redirect category
            redirect_types = [
                "Naming_redirects",
                "Alias_redirects",
                "Grammar_redirects",
                "Old_Tongue_redirects",
                "Geo-political_redirects",
                "Sword_form_redirects",
                "Chapter_redirects",
                "Date_redirects",
                "Timeline_redirects",
                "Book_redirects",
                "Category_redirects",
                "Inclusion_redirects",
                "Administrative_redirects",
                "Real-world_redirects",
            ]
            return any(rtype in content for rtype in redirect_types)
    except Exception as e:
        logger.warning(f"Error reading {file_path.name}: {e}")
        return False

def extract_page_name(file_path: Path) -> Optional[str]:
    """Extract page name from wiki file H1 header."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# ') and not line.startswith('##'):
                    page_name = line[2:].strip()
                    return page_name
        logger.warning(f"No H1 header found in {file_path.name}")
        return None
    except Exception as e:
        logger.warning(f"Error extracting page name from {file_path.name}: {e}")
        return None


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


def save_progress(mapping: Dict[str, str], output_path: Path):
    """Save progress to a temporary file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        logger.debug(f"Progress saved: {len(mapping)} mappings")
    except Exception as e:
        logger.warning(f"Could not save progress: {e}")


def build_redirect_mapping(wiki_path: Path) -> Dict[str, str]:
    """Build complete redirect mapping from wiki files."""
    mapping = {}
    errors = []
    
    wiki_files = list(wiki_path.glob("*.txt"))
    total_files = len(wiki_files)
    
    logger.info(f"Scanning {total_files} wiki files for redirects...")
    
    redirect_count = 0
    processed_count = 0
    
    for i, file_path in enumerate(wiki_files, 1):
        if i % 100 == 0:
            logger.info(f"Progress: {i}/{total_files} files scanned, {redirect_count} redirects found")
        
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
        
        logger.info(f"Processing redirect [{redirect_count}]: {page_name}")
        
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
        
        if processed_count > 0 and processed_count % 50 == 0:
            save_progress(mapping, METADATA_PATH / "redirect_mapping_progress.json")
    
    logger.info("=" * 60)
    logger.info(f"Redirect mapping complete!")
    logger.info(f"Total files scanned: {total_files}")
    logger.info(f"Redirect pages found: {redirect_count}")
    logger.info(f"Successfully mapped: {processed_count}")
    logger.info(f"Errors: {len(errors)}")
    logger.info("=" * 60)
    
    if errors:
        logger.warning(f"\n{len(errors)} errors occurred:")
        for error in errors[:10]:
            logger.warning(f"  {error}")
        if len(errors) > 10:
            logger.warning(f"  ... and {len(errors) - 10} more errors")
    
    return mapping


def save_mapping(mapping: Dict[str, str], output_path: Path):
    """Save redirect mapping to JSON file."""
    try:
        sorted_mapping = dict(sorted(mapping.items()))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_mapping, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Redirect mapping saved to: {output_path}")
        logger.info(f"Total mappings: {len(mapping)}")
        
    except Exception as e:
        logger.error(f"Failed to save mapping: {e}")
        raise


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Dragon's Codex - Redirect Mapping Builder")
    logger.info("=" * 60)
    
    if not WIKI_PATH.exists():
        logger.error(f"Wiki directory not found: {WIKI_PATH}")
        logger.error("Please ensure wiki .txt files are in data/raw/wiki/")
        return 1
    
    wiki_files = list(WIKI_PATH.glob("*.txt"))
    if not wiki_files:
        logger.error(f"No .txt files found in {WIKI_PATH}")
        return 1
    
    logger.info(f"Wiki directory: {WIKI_PATH}")
    logger.info(f"Found {len(wiki_files)} .txt files")
    logger.info("")
    
    try:
        mapping = build_redirect_mapping(WIKI_PATH)
        
        output_path = Config().FILE_REDIRECT_MAPPING
        
        save_mapping(mapping, output_path)
        
        progress_file = METADATA_PATH / "wiki/redirect_mapping_progress.json"
        if progress_file.exists():
            progress_file.unlink()
            logger.debug("Cleaned up progress file")
        
        logger.info("")
        logger.info("✓ Redirect mapping complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)