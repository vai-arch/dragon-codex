"""
Batch Scraper for All WoT Characters using the results of download_all_wiki_page_titles.py

Uses the enhanced scraper from the script wiki_scraper.py to get all character data with infoboxes

This script will scrape all characters from a list and save enhanced markdown files.

Input: data/raw/wiki_all_page_titles.json
Output: - data/raw/wiki/*.txt
        - data/raw/wiki_original/*.txt

"""

import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_files_functions import copy_files, deserialize_object, find_files_in_folder, load_json_from_file, save_json_to_file, serialize_object
from src.utils.util_statistics import total_statistics_logging
from src.utils.wiki_constants import CATEGORIES_TO_SKIP, REDIRECT_CATEGORIES, extract_categories, extract_page_name

cfg_wiki_base_url = None

in_file_wiki_all_pages_titles_file = None
in_wiki_glossary_path = None
out_wiki_original_path = None
out_wiki_path = None
out_log_path = None
out_redirect_mapping_path = None
out_redirect_aliases_mapping_path = None


class WoTWikiScraper:
    """
    Enhanced scraper for WoT Fandom wiki using MediaWiki API
    """

    def __init__(self, cfg_wiki_base_url):
        self.base_url = cfg_wiki_base_url
        self.api_url = f"{cfg_wiki_base_url}/api.php"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DragonCodex/1.0 (Educational RAG Project)"})

    def is_redirect_page(self, file_path: Path) -> bool:
        """Check if a wiki file is a redirect page (ANY type)."""

        # Regex to find any [[Category:Something]] tags
        categories = extract_categories(file_path, None)

        if not categories:
            # No categories at all
            return True

        # Check if any category matches your redirect categories
        return any(rtype.lower() in (cat.lower() for cat in categories) for rtype in REDIRECT_CATEGORIES)

    def invert_redirect_mapping(self, mapping: str):
        """Invert redirect mapping so that each canonical page lists all its redirect aliases."""

        inverted = {}

        # Build inverted mapping
        for redirect, canonical in mapping.items():
            inverted.setdefault(canonical, []).append(redirect)

        # Sort lists for consistency
        inverted = {k: sorted(v) for k, v in inverted.items()}

        return inverted

    def query_redirect_target(self, page_name: str) -> Optional[str]:
        """Query Fandom API to get redirect target for a page."""

        try:
            serialized_name = out_wiki_original_path / f"{page_name}_REDIRECTED.bin"

            # 🔹 Load from cache if exists
            if serialized_name.exists():
                data = deserialize_object(serialized_name, log=True)
            else:
                params = {"action": "query", "titles": "", "redirects": 1, "format": "json"}
                params["titles"] = page_name

                response = requests.get(f"{cfg_wiki_base_url}/api.php", params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                time.sleep(0.5)
                serialize_object(data=data, output_file=serialized_name, log=True)

            # 🔹 Process response (same logic as before)
            if "query" in data and "redirects" in data["query"]:
                redirects = data["query"]["redirects"]
                if redirects:
                    target = redirects[0].get("to")
                    if target:
                        return target

            # print(f"  API returned no redirect for {page_name}")
            return None

        except requests.RequestException as e:
            print(f"  API request failed for {page_name}: {e}")
            return None
        except Exception as e:
            print(f"  Error processing API response for {page_name}: {e}")
            return None

    def get_page_data(self, page_title):
        """
        Get complete page data from Fandom API

        Args:
            page_title: Title of the wiki page (e.g., "Rand al'Thor")

        Returns:
            dict with all page data, or None if page doesn't exist
        """
        # print(f"Fetching: {page_title}")

        # Request 1: Get parsed HTML, categories, templates, sections
        params_html = {
            "action": "parse",
            "page": page_title,
            "format": "json",
            "prop": "text|categories|templates|sections|displaytitle",
            "disablelimitreport": 1,
            "disabletoc": 1,
        }

        response_html = self.session.get(self.api_url, params=params_html)
        data_html = response_html.json()

        # Check if page exists
        if "error" in data_html:
            print(f"  ✗ Error: {data_html['error'].get('info', 'Unknown error')}")
            return None

        if "parse" not in data_html:
            print("  ✗ No parse data returned")
            return None

        parse_data = data_html["parse"]

        # Request 2: Get raw wikitext for infobox extraction
        params_wikitext = {"action": "parse", "page": page_title, "format": "json", "prop": "wikitext"}

        response_wikitext = self.session.get(self.api_url, params=params_wikitext)
        data_wikitext = response_wikitext.json()

        wikitext = ""
        if "parse" in data_wikitext:
            wikitext = data_wikitext["parse"].get("wikitext", {}).get("*", "")

        # Compile all data
        result = {
            "title": parse_data.get("title", page_title),
            "pageid": parse_data.get("pageid"),
            "displaytitle": parse_data.get("displaytitle", page_title),
            "html": parse_data.get("text", {}).get("*", ""),
            "wikitext": wikitext,
            "categories": [cat["*"] for cat in parse_data.get("categories", [])],
            "templates": [tmpl["*"] for tmpl in parse_data.get("templates", [])],
            "sections": parse_data.get("sections", []),
            "infobox": {},
            "structured_content": {},
        }

        # Extract infobox from HTML (not wikitext - HTML has rendered infobox)
        result["infobox"] = self.extract_infobox(result["html"])

        # Parse HTML content into structured sections
        result["structured_content"] = self.parse_html_content(result["html"])

        # print(f"  ✓ Success: {len(result['categories'])} categories, {len(result['infobox'])} infobox fields, {len(result['structured_content'])} sections")

        return result

    def extract_infobox(self, html):
        """
        Extract infobox data from rendered HTML

        Args:
            html: Rendered HTML from API

        Returns:
            dict with infobox fields organized by section
        """
        soup = BeautifulSoup(html, "html.parser")

        infobox_data = {"biographical": {}, "physical": {}, "chronological": {}, "other": {}}

        # Find the portable infobox (Fandom's infobox format)
        infobox = soup.find("aside", class_="portable-infobox")

        if not infobox:
            # Try other common infobox formats
            infobox = soup.find("table", class_="infobox")

        if not infobox:
            return infobox_data

        # Extract all data items from the infobox
        # Fandom infoboxes use <div class="pi-item pi-data">
        data_items = infobox.find_all("div", class_="pi-data")

        for item in data_items:
            # Find label and value
            label_elem = item.find("h3", class_="pi-data-label")
            value_elem = item.find("div", class_="pi-data-value")

            if label_elem and value_elem:
                label = label_elem.get_text(" ", strip=True)
                value = value_elem.get_text(" ", strip=True)

                # Skip empty values
                if not value:
                    continue

                # Categorize the field
                section = self.categorize_infobox_field(label)
                infobox_data[section][label] = value

        # Also try getting section headers to better categorize
        # Fandom groups data under section headers like "Biographical Information"
        sections = infobox.find_all("section", class_="pi-item")

        for section_elem in sections:
            # Get section header
            header = section_elem.find("h2", class_="pi-header")
            section_name = "other"

            if header:
                header_text = header.get_text(" ", strip=True).lower()
                if "biographical" in header_text:
                    section_name = "biographical"
                elif "physical" in header_text:
                    section_name = "physical"
                elif "chronological" in header_text or "political" in header_text:
                    section_name = "chronological"

            # Get all data items in this section
            section_data_items = section_elem.find_all("div", class_="pi-data")

            for item in section_data_items:
                label_elem = item.find("h3", class_="pi-data-label")
                value_elem = item.find("div", class_="pi-data-value")

                if label_elem and value_elem:
                    label = label_elem.get_text(" ", strip=True)
                    value = value_elem.get_text(" ", strip=True)

                    if value:
                        # Use the section name from the header
                        infobox_data[section_name][label] = value

        return infobox_data

    def categorize_infobox_field(self, field_name):
        """
        Categorize infobox field into biographical, physical, chronological, or other

        Args:
            field_name: Name of the infobox field

        Returns:
            str: 'biographical', 'physical', 'chronological', or 'other'
        """
        field_lower = field_name.lower()

        # Biographical fields
        biographical_keywords = [
            "nationality",
            "nation",
            "status",
            "current status",
            "title",
            "rank",
            "affiliation",
            "occupation",
            "family",
            "spouse",
            "children",
            "parents",
            "siblings",
            "house",
            "clan",
            "organization",
            "allegiance",
        ]

        # Physical fields
        physical_keywords = [
            "hair",
            "eyes",
            "eye",
            "height",
            "build",
            "complexion",
            "skin",
            "appearance",
            "physical",
            "gender",
            "sex",
            "race",
            "species",
        ]

        # Chronological fields
        chronological_keywords = [
            "birth",
            "death",
            "died",
            "born",
            "first",
            "last",
            "appearance",
            "appeared",
            "mentioned",
            "pov",
            "book",
            "debut",
            "final",
        ]

        # Check exact matches first for common fields
        exact_matches = {
            "nationality": "biographical",
            "current status": "biographical",
            "status": "biographical",
            "title": "biographical",
            "affiliation": "biographical",
            "gender": "physical",
            "height": "physical",
            "build": "physical",
            "first appeared": "chronological",
            "last appeared": "chronological",
            "first appearance": "chronological",
            "last appearance": "chronological",
        }

        if field_lower in exact_matches:
            return exact_matches[field_lower]

        # Check keyword matches
        for keyword in biographical_keywords:
            if keyword in field_lower:
                return "biographical"

        for keyword in physical_keywords:
            if keyword in field_lower:
                return "physical"

        for keyword in chronological_keywords:
            if keyword in field_lower:
                return "chronological"

        return "other"

    def clean_wiki_markup(self, text):
        """
        Clean wiki markup from text

        Args:
            text: Text with wiki markup

        Returns:
            str: Cleaned text
        """
        # Remove HTML comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Convert wiki links [[Link|Display]] to Display (or Link if no |)
        text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
        text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

        # Remove external links [http://example.com Text] to Text
        text = re.sub(r"\[http[^\s]+ ([^\]]+)\]", r"\1", text)

        # Remove file/image links
        text = re.sub(r"\[\[File:.*?\]\]", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\[\[Image:.*?\]\]", "", text, flags=re.IGNORECASE)

        # Remove bold/italic markup
        text = re.sub(r"'{2,}", "", text)

        # Remove templates {{Template}}
        text = re.sub(r"\{\{[^\}]*\}\}", "", text)

        # Remove <ref> tags
        text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<ref[^>]*/?>", "", text, flags=re.IGNORECASE)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def parse_html_content(self, html):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        sections = {}
        current_section = "Overview"
        current_content = []

        content = soup.find("div", class_="mw-parser-output") or soup

        # Remove junk elements
        for tag in content.find_all(["aside", "div", "table"], class_=["portable-infobox", "navbox", "wikitable"]):
            tag.decompose()

        # Iterate through top-level children
        for elem in content.children:
            if not hasattr(elem, "name"):
                continue
            if elem.name in ("script", "style"):
                continue

            # -------------------------------
            # H2 — main section title
            # -------------------------------
            if elem.name == "h2":
                if current_content:
                    sections[current_section] = "\n\n".join(current_content)

                span = elem.find("span", class_="mw-headline")
                if span:
                    title = span.get_text(" ", strip=True)
                    if title.lower() not in ["contents", "references", "notes"]:
                        current_section = title
                        current_content = []
                continue

            # -------------------------------
            # H3 — subsection title
            # -------------------------------
            if elem.name == "h3":
                span = elem.find("span", class_="mw-headline")
                if span:
                    subtitle = span.get_text(" ", strip=True)
                    if subtitle.lower() not in ["references", "notes"]:
                        current_content.append(f"### {subtitle}")
                continue

            # -------------------------------
            # Paragraphs
            # -------------------------------
            if elem.name == "p":
                text = elem.get_text(" ", strip=True)

                # Remove numeric citations [9], [ 14 ], etc.
                text = re.sub(r"\[\s*\d+\s*\]", "", text)

                # Remove all bracketed citation-like text [citation needed], etc.
                text = re.sub(r"\[\s*[^\]]+\s*\]", "", text)

                # Collapse multiple spaces created after removing citations
                text = re.sub(r"\s{2,}", " ", text).strip()

                # Fix leftover " ." / " ," / " ?" etc.
                text = re.sub(r"\s+([.,!?;:])", r"\1", text)

                # Keep chapter titles + content after h3
                if text and len(text) > 2:
                    current_content.append(text)

                continue

            # -------------------------------
            # Lists (ul/ol)
            # -------------------------------
            if elem.name in ("ul", "ol"):
                list_items = []
                for li in elem.find_all("li", recursive=False):
                    t = li.get_text(" ", strip=True)
                    if t:
                        list_items.append(f"- {t}")
                if list_items:
                    current_content.append("\n".join(list_items))
                continue

            # -------------------------------
            # Definition Lists (dl)
            # -------------------------------
            if elem.name == "dl":
                dl_items = []
                for child in elem.children:
                    if not hasattr(child, "name"):
                        continue

                    if child.name == "dt":
                        # Definition term (usually bold labels)
                        term = child.get_text(" ", strip=True)
                        if term:
                            dl_items.append(f"**{term}**")

                    elif child.name == "dd":
                        # Definition description (the actual content)
                        desc = child.get_text(" ", strip=True)
                        if desc:
                            dl_items.append(desc)

                if dl_items:
                    current_content.append("\n\n".join(dl_items))
                continue

        # Save final section
        if current_content:
            sections[current_section] = "\n\n".join(current_content)

        return sections

    def save_as_markdown(self, page_data, output_path):
        """
        Save complete page data as enhanced markdown

        Args:
            page_data: dict from get_page_data
            output_path: Path object where to save
        """
        lines = []

        # Title
        lines.append(f"# {page_data['title']}")
        lines.append("")

        # Metadata comment
        lines.append("<!-- Metadata -->")
        lines.append(f"<!-- Page ID: {page_data.get('pageid', 'unknown')} -->")
        if page_data["categories"]:
            lines.append(f"<!-- Categories: {', '.join(page_data['categories'])} -->")
        lines.append("")

        # Infobox as structured data
        if any(page_data["infobox"].values()):
            lines.append("## Information")
            lines.append("")

            # Order: biographical, physical, chronological, other
            section_order = ["biographical", "physical", "chronological", "other"]

            for section_name in section_order:
                section_data = page_data["infobox"].get(section_name, {})
                if section_data:
                    lines.append(f"### {section_name.title()} Information")
                    lines.append("")
                    for label, value in section_data.items():
                        lines.append(f"**{label}:** {value}  ")
                    lines.append("")

        # Categories as tags
        if page_data["categories"]:
            lines.append("## Categories")
            lines.append("")
            # Show first 20, then indicate more
            cats_to_show = page_data["categories"][:20]
            lines.append(", ".join(cats_to_show))
            if len(page_data["categories"]) > 20:
                lines.append(f"\n*...and {len(page_data['categories']) - 20} more categories*")
            lines.append("")

        # Main content sections
        lines.append("---")
        lines.append("")

        for section_name, section_content in page_data["structured_content"].items():
            lines.append(f"## {section_name}")
            lines.append("")
            lines.append(section_content)
            lines.append("")

        # Save to file
        markdown_text = "\n".join(lines)
        output_path.write_text(markdown_text, encoding="utf-8")

    def scrape_wiki_pages(self, page_names, output_dir, delay=1.0):
        """
        Scrape a list of pages and save as markdown

        Args:
            character_names: List of page names or URLs
            output_dir: Directory to save markdown files
            delay: Seconds to wait between requests (be nice to server)

        Returns:
            dict with statistics
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check for existing files (case-insensitive tracking)
        existing_files = set(f.stem for f in output_dir.glob("*.txt"))
        existing_files_lower = {name.lower(): name for name in existing_files}

        stats = {
            "total": len(page_names),
            "success": 0,
            "failed": 0,
            "existing": 0,
            "skipped": 0,
            "collision": 0,
            "lower_size": 0,
        }

        errors = []
        collision_log = []

        print(f"\nScraping {len(page_names)} pages...")
        if existing_files:
            print(f"Found {len(existing_files)} existing files - will skip those")
        print(f"Output directory: {output_dir}\n")

        for char_name in tqdm(page_names, desc="Scraping"):
            try:
                # Handle both plain names and dicts with 'name' or 'title' key
                if isinstance(char_name, dict):
                    char_name = char_name.get("name", char_name.get("title", ""))

                if not char_name:
                    continue

                # Create safe filename
                safe_filename = char_name.replace(" ", "_").replace("/", "_")
                safe_filename = re.sub(r'[<>:"|?*]', "", safe_filename)

                # Check if already exists
                if safe_filename in existing_files:
                    stats["existing"] += 1
                    continue

                if f"{safe_filename}_SKIPPED" in existing_files:
                    stats["skipped"] += 1
                    continue

                # Get page data
                page_data = self.get_page_data(char_name)

                if page_data is None:
                    stats["failed"] += 1
                    errors.append(f"{char_name}: Page not found")
                    continue

                # Update safe filename from actual title
                safe_filename = page_data["title"].replace(" ", "_").replace("/", "_")
                safe_filename = re.sub(r'[<>:"|?*]', "", safe_filename)

                safe_filename_lower = safe_filename.lower()

                page_categories = {c.lower() for c in page_data.get("categories", [])}
                skip_categories_lower = {c.lower() for c in CATEGORIES_TO_SKIP}

                if page_categories & skip_categories_lower or str(page_data["title"]).startswith("Stedding "):
                    # Found at least one category to skip
                    stats["skipped"] += 1
                    # print(f"  → Skipped (blocked categories match): {char_name}")
                    safe_filename_lower = f"{safe_filename_lower}_SKIPPED.txt"
                    final_path = output_dir / f"{safe_filename}_SKIPPED.txt"
                else:
                    final_path = output_dir / f"{safe_filename}.txt"

                # If file already exists (case-insensitive)
                if safe_filename_lower in existing_files_lower:
                    original_name = existing_files_lower[safe_filename_lower]
                    final_path = output_dir / f"{original_name}.txt"

                    # Write new content to temp file first
                    with NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                        tmp_path = Path(tmp.name)

                    self.save_as_markdown(page_data, tmp_path)

                    new_size = tmp_path.stat().st_size
                    existing_size = final_path.stat().st_size

                    if new_size <= existing_size:
                        # Skip if new file is smaller or equal
                        tmp_path.unlink()
                        stats["collision"] += 1
                        collision_log.append(f"{char_name} -> {safe_filename} skipped ({new_size} <= {existing_size})")
                        continue

                    # Overwrite existing file (atomic)
                    tmp_path.replace(final_path)

                    stats["collision"] += 1
                    collision_log.append(f"{char_name} -> {safe_filename} overwritten ({new_size} > {existing_size})")
                else:
                    # No collision → write directly
                    self.save_as_markdown(page_data, final_path)

                # Update tracking (add new filename to existing files)
                existing_files.add(safe_filename)
                existing_files_lower[safe_filename.lower()] = safe_filename

                stats["success"] += 1

                # Be nice to the server
                time.sleep(delay)

            except Exception as e:
                stats["failed"] += 1
                print(f"\n  ✗ Error with {char_name}: {e}")
                traceback.print_exc()  # optional: prints full stack trace
                continue

        if stats["skipped"] > 0:
            print(f"\n✓ Skipped {stats['skipped']} existing files")

        if stats["collision"] > 0:
            print(f"\n⚠️  {stats['collision']} case collisions detected and resolved")

            # Save collision log
            collision_log_file = out_log_path / "case_collision.log"
            with open(collision_log_file, "w", encoding="utf-8") as f:
                f.write("CASE COLLISION LOG\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Total collisions: {stats['collision']}\n\n")
                for entry in collision_log:
                    f.write(entry + "\n")
            print(f"   Collision log saved to: {collision_log_file}")

        return stats

    def build_redirect_mapping(self, wiki_path: Path) -> Dict[str, str]:
        """Build complete redirect mapping from wiki files."""
        mapping = {}
        errors = []

        wiki_files = find_files_in_folder(wiki_path, ".txt", recursive=False)

        redirect_count = 0
        processed_count = 0

        pbar = tqdm(
            total=len(wiki_files),
            desc="Scanning wiki files",
            unit="file",
            file=sys.stderr,  # 👈 IMPORTANT
            mininterval=0.0,  # 👈 FORCE refresh
        )

        for file_path in wiki_files:
            pbar.update(1)
            if not self.is_redirect_page(file_path):
                continue

            redirect_count += 1

            page_name = extract_page_name(file_path)
            if not page_name:
                errors.append({"file": file_path.name, "error": "Could not extract page name"})
                continue

            target = self.query_redirect_target(page_name)

            if target:
                mapping[page_name] = target
                processed_count += 1
            else:
                errors.append({"file": file_path.name, "page_name": page_name, "error": "API query failed or returned no redirect"})

        if errors:
            print(f"\n{len(errors)} errors occurred:")
            for error in errors[:10000]:
                print(f"  {error}")
            if len(errors) > 10000:
                print(f"  ... and {len(errors) - 10000} more errors")

        # fmt: off
        statistics = {
            "redirected_pages": redirect_count,
            "redirections_mapped": processed_count,
            "redirections_errors": len(errors)
        }
        # fmt: on
        return dict(sorted(mapping.items())), statistics


def main():
    start_time = datetime.now()

    pages = load_json_from_file(in_file_wiki_all_pages_titles_file)

    # Create scraper
    scraper = WoTWikiScraper(cfg_wiki_base_url)

    # Scrape all pages
    metrics = scraper.scrape_wiki_pages(page_names=pages, output_dir=out_wiki_original_path, delay=1.0)

    # After scraping, copy files to final directory
    copy_files(out_wiki_original_path, out_wiki_path, extension=".txt", log=False, exclude_pattern="*_SKIPPED.txt")
    copy_files(in_wiki_glossary_path, out_wiki_path, extension=".txt", log=False)

    # build redirects
    redirect_mapping, redirect_statistics = scraper.build_redirect_mapping(out_wiki_path)
    save_json_to_file(redirect_mapping, out_redirect_mapping_path, indent=2)
    aliases = scraper.invert_redirect_mapping(redirect_mapping)
    save_json_to_file(aliases, out_redirect_aliases_mapping_path, indent=2)

    # fmt:off
    statistics = {
        "name": "scrapped_pages", 
        "metrics": metrics
    }

    statistics["metrics"] = {**statistics["metrics"], **redirect_statistics}
        # fmt:on

    total_time = datetime.now() - start_time

    total_statistics_logging(total_time=total_time, log_name="ing_03_wiki_scrapper", statistics=statistics, title="SCRAPPED PAGES")


if __name__ == "__main__":
    config = get_config()
    paths = get_paths()

    cfg_wiki_base_url = config.WIKI_BASE_URL
    in_file_wiki_all_pages_titles_file = paths.FILE_WIKI_ALL_PAGE_TITLES
    in_wiki_glossary_path = paths.WIKI_GLOSSARY_PATH
    out_wiki_original_path = paths.WIKI_ORIGINAL_PATH
    out_wiki_path = paths.WIKI_PATH
    out_log_path = paths.LOG_PATH
    out_redirect_mapping_path = paths.FILE_REDIRECT_MAPPING
    out_redirect_aliases_mapping_path = paths.FILE_REDIRECT_ALIASES_MAPPING

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
