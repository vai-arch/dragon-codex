"""
Enhanced WoT Wiki Scraper using MediaWiki API
Gets complete information including infoboxes, categories, and full content

This script uses the Fandom MediaWiki API to extract:
- Main article content (HTML and wikitext)
- Infobox data (biographical, physical, chronological)
- Categories
- All sections and subsections
- Templates used

Author: Dragon's Codex Project
Date: Week 1 Session 2
"""

import requests
import json
import re
import time
from pathlib import Path
from src.utils.config import Config
from bs4 import BeautifulSoup
from tqdm import tqdm
from src.utils.wiki_constants import CATEGORIES_TO_SKIP

class WoTWikiScraper:
    """
    Enhanced scraper for WoT Fandom wiki using MediaWiki API
    """
    
    def __init__(self, base_url=Config().WIKI_BASE_URL):
        self.base_url = base_url
        self.api_url = f"{base_url}/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DragonCodex/1.0 (Educational RAG Project)'
        })
    
    def get_page_data(self, page_title):
        """
        Get complete page data from Fandom API
        
        Args:
            page_title: Title of the wiki page (e.g., "Rand al'Thor")
        
        Returns:
            dict with all page data, or None if page doesn't exist
        """
        print(f"Fetching: {page_title}")
        
        # Request 1: Get parsed HTML, categories, templates, sections
        params_html = {
            'action': 'parse',
            'page': page_title,
            'format': 'json',
            'prop': 'text|categories|templates|sections|displaytitle',
            'disablelimitreport': 1,
            'disabletoc': 1
        }
        
        response_html = self.session.get(self.api_url, params=params_html)
        data_html = response_html.json()
        
        # Check if page exists
        if 'error' in data_html:
            print(f"  ✗ Error: {data_html['error'].get('info', 'Unknown error')}")
            return None
        
        if 'parse' not in data_html:
            print(f"  ✗ No parse data returned")
            return None
        
        parse_data = data_html['parse']
        
        # Request 2: Get raw wikitext for infobox extraction
        params_wikitext = {
            'action': 'parse',
            'page': page_title,
            'format': 'json',
            'prop': 'wikitext'
        }
        
        response_wikitext = self.session.get(self.api_url, params=params_wikitext)
        data_wikitext = response_wikitext.json()
        
        wikitext = ''
        if 'parse' in data_wikitext:
            wikitext = data_wikitext['parse'].get('wikitext', {}).get('*', '')
        
        # Compile all data
        result = {
            'title': parse_data.get('title', page_title),
            'pageid': parse_data.get('pageid'),
            'displaytitle': parse_data.get('displaytitle', page_title),
            'html': parse_data.get('text', {}).get('*', ''),
            'wikitext': wikitext,
            'categories': [cat['*'] for cat in parse_data.get('categories', [])],
            'templates': [tmpl['*'] for tmpl in parse_data.get('templates', [])],
            'sections': parse_data.get('sections', []),
            'infobox': {},
            'structured_content': {}
        }
        
        # Extract infobox from HTML (not wikitext - HTML has rendered infobox)
        result['infobox'] = self.extract_infobox(result['html'])
        
        # Parse HTML content into structured sections
        result['structured_content'] = self.parse_html_content(result['html'])
        
        print(f"  ✓ Success: {len(result['categories'])} categories, "
              f"{len(result['infobox'])} infobox fields, "
              f"{len(result['structured_content'])} sections")
        
        return result
    
    def extract_infobox(self, html):
        """
        Extract infobox data from rendered HTML
        
        Args:
            html: Rendered HTML from API
        
        Returns:
            dict with infobox fields organized by section
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        infobox_data = {
            'biographical': {},
            'physical': {},
            'chronological': {},
            'other': {}
        }
        
        # Find the portable infobox (Fandom's infobox format)
        infobox = soup.find('aside', class_='portable-infobox')
        
        if not infobox:
            # Try other common infobox formats
            infobox = soup.find('table', class_='infobox')
        
        if not infobox:
            return infobox_data
        
        # Extract all data items from the infobox
        # Fandom infoboxes use <div class="pi-item pi-data">
        data_items = infobox.find_all('div', class_='pi-data')
        
        for item in data_items:
            # Find label and value
            label_elem = item.find('h3', class_='pi-data-label')
            value_elem = item.find('div', class_='pi-data-value')
            
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
        sections = infobox.find_all('section', class_='pi-item')
        
        for section_elem in sections:
            # Get section header
            header = section_elem.find('h2', class_='pi-header')
            section_name = 'other'
            
            if header:
                header_text = header.get_text(" ", strip=True).lower()
                if 'biographical' in header_text:
                    section_name = 'biographical'
                elif 'physical' in header_text:
                    section_name = 'physical'
                elif 'chronological' in header_text or 'political' in header_text:
                    section_name = 'chronological'
            
            # Get all data items in this section
            section_data_items = section_elem.find_all('div', class_='pi-data')
            
            for item in section_data_items:
                label_elem = item.find('h3', class_='pi-data-label')
                value_elem = item.find('div', class_='pi-data-value')
                
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
            'nationality', 'nation', 'status', 'current status', 'title', 'rank', 
            'affiliation', 'occupation', 'family', 'spouse', 'children', 'parents', 
            'siblings', 'house', 'clan', 'organization', 'allegiance'
        ]
        
        # Physical fields
        physical_keywords = [
            'hair', 'eyes', 'eye', 'height', 'build', 'complexion', 'skin',
            'appearance', 'physical', 'gender', 'sex', 'race', 'species'
        ]
        
        # Chronological fields  
        chronological_keywords = [
            'birth', 'death', 'died', 'born', 'first', 'last', 'appearance',
            'appeared', 'mentioned', 'pov', 'book', 'debut', 'final'
        ]
        
        # Check exact matches first for common fields
        exact_matches = {
            'nationality': 'biographical',
            'current status': 'biographical',
            'status': 'biographical',
            'title': 'biographical',
            'affiliation': 'biographical',
            'gender': 'physical',
            'height': 'physical',
            'build': 'physical',
            'first appeared': 'chronological',
            'last appeared': 'chronological',
            'first appearance': 'chronological',
            'last appearance': 'chronological'
        }
        
        if field_lower in exact_matches:
            return exact_matches[field_lower]
        
        # Check keyword matches
        for keyword in biographical_keywords:
            if keyword in field_lower:
                return 'biographical'
        
        for keyword in physical_keywords:
            if keyword in field_lower:
                return 'physical'
        
        for keyword in chronological_keywords:
            if keyword in field_lower:
                return 'chronological'
        
        return 'other'
    
    def clean_wiki_markup(self, text):
        """
        Clean wiki markup from text
        
        Args:
            text: Text with wiki markup
        
        Returns:
            str: Cleaned text
        """
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        
        # Convert wiki links [[Link|Display]] to Display (or Link if no |)
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        
        # Remove external links [http://example.com Text] to Text
        text = re.sub(r'\[http[^\s]+ ([^\]]+)\]', r'\1', text)
        
        # Remove file/image links
        text = re.sub(r'\[\[File:.*?\]\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[\[Image:.*?\]\]', '', text, flags=re.IGNORECASE)
        
        # Remove bold/italic markup
        text = re.sub(r"'{2,}", '', text)
        
        # Remove templates {{Template}}
        text = re.sub(r'\{\{[^\}]*\}\}', '', text)
        
        # Remove <ref> tags
        text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<ref[^>]*/?>', '', text, flags=re.IGNORECASE)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def parse_html_content(self, html):
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        sections = {}
        current_section = "Overview"
        current_content = []
        last_header = None

        content = soup.find("div", class_="mw-parser-output") or soup

        # Remove junk elements
        for tag in content.find_all(["aside", "div", "table"], 
                                class_=["portable-infobox", "navbox", "wikitable"]):
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
                        last_header = None
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
                        last_header = "h3"
                continue

            # -------------------------------
            # Paragraphs
            # -------------------------------
            if elem.name == "p":
                text = elem.get_text(" ", strip=True)

                # Remove numeric citations [9], [ 14 ], etc.
                text = re.sub(r'\[\s*\d+\s*\]', '', text)

                # Remove all bracketed citation-like text [citation needed], etc.
                text = re.sub(r'\[\s*[^\]]+\s*\]', '', text)

                # Collapse multiple spaces created after removing citations
                text = re.sub(r'\s{2,}', ' ', text).strip()

                # Fix leftover " ." / " ," / " ?" etc.
                text = re.sub(r'\s+([.,!?;:])', r'\1', text)
                
                # Keep chapter titles + content after h3
                if text and len(text) > 2:
                    current_content.append(text)

                last_header = None
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
                last_header = None
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
                last_header = None
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
        if page_data['categories']:
            lines.append(f"<!-- Categories: {', '.join(page_data['categories'])} -->")
        lines.append("")
        
        # Infobox as structured data
        if any(page_data['infobox'].values()):
            lines.append("## Information")
            lines.append("")
            
            # Order: biographical, physical, chronological, other
            section_order = ['biographical', 'physical', 'chronological', 'other']
            
            for section_name in section_order:
                section_data = page_data['infobox'].get(section_name, {})
                if section_data:
                    lines.append(f"### {section_name.title()} Information")
                    lines.append("")
                    for label, value in section_data.items():
                        lines.append(f"**{label}:** {value}  ")
                    lines.append("")
        
        # Categories as tags
        if page_data['categories']:
            lines.append("## Categories")
            lines.append("")
            # Show first 20, then indicate more
            cats_to_show = page_data['categories'][:20]
            lines.append(", ".join(cats_to_show))
            if len(page_data['categories']) > 20:
                lines.append(f"\n*...and {len(page_data['categories']) - 20} more categories*")
            lines.append("")
        
        # Main content sections
        lines.append("---")
        lines.append("")
        
        for section_name, section_content in page_data['structured_content'].items():
            lines.append(f"## {section_name}")
            lines.append("")
            lines.append(section_content)
            lines.append("")
        
        # Save to file
        markdown_text = '\n'.join(lines)
        output_path.write_text(markdown_text, encoding='utf-8')
    
    def scrape_character_list(self, character_names, output_dir, delay=1.0):
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
        existing_files = set(f.stem for f in output_dir.glob('*.txt'))
        existing_files_lower = {name.lower(): name for name in existing_files}
        
        stats = {
            'total': len(character_names),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'collisions': 0,
            'errors': [],
            'collision_log': []
        }
        
        print(f"\nScraping {len(character_names)} pages...")
        if existing_files:
            print(f"Found {len(existing_files)} existing files - will skip those")
        print(f"Output directory: {output_dir}\n")
        
        for char_name in tqdm(character_names, desc="Scraping"):
            try:
                # Handle both plain names and dicts with 'name' or 'title' key
                if isinstance(char_name, dict):
                    char_name = char_name.get('name', char_name.get('title', ''))
                
                if not char_name:
                    continue
                
                # Create safe filename
                safe_filename = char_name.replace(' ', '_').replace('/', '_')
                safe_filename = re.sub(r'[<>:"|?*]', '', safe_filename)
                
                # Check if already exists
                if safe_filename in existing_files:
                    stats['skipped'] += 1
                    continue
                
                # Get page data
                page_data = self.get_page_data(char_name)
                
                if page_data is None:
                    stats['failed'] += 1
                    stats['errors'].append(f"{char_name}: Page not found")
                    continue
                
                page_categories = {c.lower() for c in page_data.get("categories", [])}
                skip_categories_lower = {c.lower() for c in CATEGORIES_TO_SKIP}

                if page_categories & skip_categories_lower:
                    # Found at least one category to skip
                    stats["skipped"] += 1
                    print(f"  → Skipped (blocked categories match): {char_name}")
                    continue

                # Update safe filename from actual title
                safe_filename = page_data['title'].replace(' ', '_').replace('/', '_')
                safe_filename = re.sub(r'[<>:"|?*]', '', safe_filename)
                
                # Check for case-insensitive collision (Windows issue)
                safe_filename_lower = safe_filename.lower()
                if safe_filename_lower in existing_files_lower:
                    # Collision detected! Add duplicate suffix
                    original_name = existing_files_lower[safe_filename_lower]
                    collision_info = f"{char_name} -> {safe_filename} (collides with {original_name})"
                    
                    # Find next available suffix number
                    suffix_num = 1
                    while True:
                        test_name = f"{safe_filename}_DUPLICATE_{suffix_num}"
                        if test_name.lower() not in existing_files_lower:
                            safe_filename = test_name
                            break
                        suffix_num += 1
                    
                    stats['collisions'] += 1
                    stats['collision_log'].append(collision_info + f" -> saved as {safe_filename}")
                    print(f"\n  ⚠️  COLLISION: {collision_info}")
                    print(f"      Saving as: {safe_filename}.txt")
                
                output_path = output_dir / f"{safe_filename}.txt"
                
                # Save markdown
                self.save_as_markdown(page_data, output_path)
                
                # Update tracking (add new filename to existing files)
                existing_files.add(safe_filename)
                existing_files_lower[safe_filename.lower()] = safe_filename
                
                stats['success'] += 1
                
                # Be nice to the server
                time.sleep(delay)
                
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"{char_name}: {str(e)}")
                print(f"\n  ✗ Error with {char_name}: {e}")
                continue
        
        if stats['skipped'] > 0:
            print(f"\n✓ Skipped {stats['skipped']} existing files")
        
        if stats['collisions'] > 0:
            print(f"\n⚠️  {stats['collisions']} case collisions detected and resolved")
            
            # Save collision log
            collision_log_file = output_dir / 'case_collisions.log'
            with open(collision_log_file, 'w', encoding='utf-8') as f:
                f.write("CASE COLLISION LOG\n")
                f.write("="*80 + "\n\n")
                f.write(f"Total collisions: {stats['collisions']}\n\n")
                for entry in stats['collision_log']:
                    f.write(entry + "\n")
            print(f"   Collision log saved to: {collision_log_file}")
        
        return stats


def main():
    """
    Main function - test scraper with example character
    """
    scraper = WoTWikiScraper()
    
    # Test with Ailil Riatin (the problematic example)
    print("="*60)
    print("Testing Enhanced WoT Wiki Scraper")
    print("="*60)
    
    test_character = "Karaethon_Cycle"
    
    # Get data
    data = scraper.get_page_data(test_character)
    
    if data:
        print("\n" + "="*60)
        print("EXTRACTION RESULTS")
        print("="*60)
        
        print(f"\nTitle: {data['title']}")
        print(f"Page ID: {data.get('pageid')}")
        
        print(f"\nCategories ({len(data['categories'])}):")
        for cat in data['categories'][:10]:  # First 10
            print(f"  - {cat}")
        if len(data['categories']) > 10:
            print(f"  ... and {len(data['categories']) - 10} more")
        
        print("\nInfobox Data:")
        for section_name, section_data in data['infobox'].items():
            if section_data:
                print(f"\n  {section_name.title()} ({len(section_data)} fields):")
                for key, value in list(section_data.items())[:5]:  # First 5
                    print(f"    {key}: {value}")
                if len(section_data) > 5:
                    print(f"    ... and {len(section_data) - 5} more fields")
        
        print(f"\nContent Sections ({len(data['structured_content'])}):")
        for section in data['structured_content'].keys():
            print(f"  - {section}")
        
        # Save example
        output_path = Path("test_rand.txt")
        scraper.save_as_markdown(data, output_path)
        print(f"\n✓ Saved enhanced markdown to: {output_path}")
        
        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print("\nThe enhanced scraper is working correctly.")
        print("You can now use it to scrape all your characters.")
    
    else:
        print("\n✗ Failed to get data")


if __name__ == "__main__":
    main()