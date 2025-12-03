"""
Prophecy & Magic System Extractor - Week 3 Goal 4
Extracts structured prophecy and magic system data from wiki concepts.

This script:
1. Loads wiki_concept.json
2. Filters prophecy and magic system pages
3. Extracts structured data (descriptions, practitioners, related terms)
4. Saves to prophecy_index.json and magic_system_index.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.config import get_config


class ProphecyMagicExtractor:
    """Extracts prophecy and magic system data from wiki concepts."""
    
    def __init__(self):
        """Initialize extractor with config."""
        self.config = get_config()
        
        # Define page lists
        self.prophecy_pages = [
            'Foretelling.txt',
            "Min's_viewings.txt",
            'Jendai_Prophecy.txt',
            'Prophecy_of_Rhuidean.txt',
            "Reo_Myershi's_prophecy.txt",
            'Black_Tower_Foretelling.txt'
        ]
        
        self.magic_pages = [
            # Core concepts
            'One_Power.txt', 'Saidin.txt', 'Saidar.txt', 'Channeling.txt',
            'True_Power.txt', 'Five_Powers.txt', 'Weave.txt',
            
            # Objects
            'Angreal.txt', "Sa'angreal.txt", "Ter'angreal.txt",
            'Fat_bald_man_angreal.txt', 'Robed_woman_angreal.txt',
            "Vora's_sa'angreal.txt",
            
            # Specific ter'angreal
            "Air_Pulse_ter'angreal.txt", "Dart_ter'angreal.txt",
            "Fancloth_ter'angreal.txt", "Fireball_ter'angreal.txt",
            "Fire_Shield_ter'angreal.txt", "Heal_ter'angreal.txt",
            "Peaceful_illusions_ter'angreal.txt", "Reading_ter'angreal.txt",
            "Shift_ter'angreal.txt",
            
            # Talents and abilities
            'Channeling_sickness.txt', 'Cleansing_of_saidin.txt',
            'Cutting_weaves.txt', 'Masking_the_Power.txt',
            
            # Weaves
            'Dawnweave.txt', 'Sleepweaver.txt',
            
            # Strength and rankings
            'Strength_in_the_One_Power.txt',
            'Strength_in_the_One_Power_among_Aes_Sedai.txt',
            'Strength_in_the_One_Power_among_the_Kin.txt',
            'Strength_in_the_One_Power_among_the_Wise_Ones.txt',
            'Strength_in_the_One_Power_rankings.txt',
            
            # Other
            'First_Weaver.txt', 'Power-wrought.txt',
            "Making_ter'angreal.txt", 'War_of_Power.txt',
            'A_Study_of_Men,_Women_and_the_One_Power_Among_Humans.txt',
            "Magical_Artifacts_Sa'angreal,_Ter'angreal,_and_Angreal.txt",
            'The_Proper_Taming_of_Power.txt'
        ]
    
    def extract_overview(self, sections: List[Dict]) -> str:
        """Extract overview/description from sections."""
        for section in sections:
            if section.get('title', '').lower() in ['overview', 'description']:
                return section.get('content', '').strip()
        
        # If no overview section, try first non-category section
        for section in sections:
            title = section.get('title', '').lower()
            if title not in ['categories', 'see also', 'external links', 'references']:
                content = section.get('content', '').strip()
                if len(content) > 50:  # Minimum length for valid description
                    return content
        
        return ""
    
    def extract_list_items(self, content: str) -> List[str]:
        """Extract list items from content (bullet points or line breaks)."""
        items = []
        
        # Try bullet points first
        bullet_pattern = r'[-•*]\s*(.+?)(?=\n|$)'
        matches = re.findall(bullet_pattern, content)
        if matches:
            items = [m.strip() for m in matches if m.strip()]
            return items
        
        # Try line breaks
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:
                # Remove common prefixes
                line = re.sub(r'^[-•*]\s*', '', line)
                items.append(line)
        
        return items
    
    def extract_character_mentions(self, content: str) -> List[str]:
        """Extract character names from content (simple heuristic)."""
        # This is a simplified version - could be enhanced with character_index
        # For now, look for capitalized words that might be names
        
        if not content:
            return []
        
        # Pattern: Capitalized words (2+ chars)
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.findall(pattern, content)
        
        # Filter out common words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 
                       'What', 'Who', 'Why', 'How', 'Book', 'Chapter', 'See', 'Also',
                       'Main', 'Article', 'Page', 'In', 'Of', 'And', 'Or', 'But', 'For',
                       'With', 'From', 'By', 'At', 'To', 'As', 'On', 'Into', 'Through'}
        
        names = [m for m in matches if m not in common_words and len(m) > 3]
        
        # Return unique names
        return sorted(list(set(names)))
    
    def categorize_magic_page(self, filename: str, sections: List[Dict]) -> str:
        """Categorize magic system page by type."""
        filename_lower = filename.lower()
        
        # Check filename patterns
        if 'angreal' in filename_lower or 'ter' in filename_lower:
            return 'Object'
        elif 'weave' in filename_lower or 'dawnweave' in filename_lower or 'sleepweaver' in filename_lower:
            return 'Weave'
        elif 'strength' in filename_lower or 'ranking' in filename_lower:
            return 'Strength_Ranking'
        elif any(x in filename_lower for x in ['saidin', 'saidar', 'one_power', 'channeling', 'true_power']):
            return 'Core_Concept'
        elif 'talent' in filename_lower or 'ability' in filename_lower:
            return 'Talent'
        else:
            return 'Other'
    
    def extract_prophecy_data(self, page_data: Dict) -> Dict:
        """Extract structured data from prophecy page."""
        sections = page_data.get('sections', [])
        page_name = page_data.get('page_name', '')
        filename = page_data.get('filename', '')
        
        # Extract overview
        description = self.extract_overview(sections)
        
        # Find practitioners/people section
        practitioners = []
        for section in sections:
            title = section.get('title', '').lower()
            if any(keyword in title for keyword in ['people', 'practitioner', 'possessing', 'who']):
                content = section.get('content', '')
                practitioners = self.extract_list_items(content)
                break
        
        # Extract all character mentions from overview
        related_characters = self.extract_character_mentions(description)
        
        # Determine type
        prophecy_type = 'Unknown'
        if 'foretelling' in page_name.lower():
            prophecy_type = 'Foretelling'
        elif 'viewing' in page_name.lower():
            prophecy_type = 'Viewing'
        elif 'prophecy' in page_name.lower():
            prophecy_type = 'Prophecy'
        
        return {
            'type': prophecy_type,
            'description': description,
            'practitioners': practitioners,
            'related_characters': related_characters,
            'source_file': filename,
            'full_sections': sections  # Keep for reference
        }
    
    def extract_magic_data(self, page_data: Dict) -> Dict:
        """Extract structured data from magic system page."""
        sections = page_data.get('sections', [])
        page_name = page_data.get('page_name', '')
        filename = page_data.get('filename', '')
        
        # Extract overview
        description = self.extract_overview(sections)
        
        # Categorize
        category = self.categorize_magic_page(filename, sections)
        
        # Extract related terms from content
        related_terms = set()
        for section in sections:
            content = section.get('content', '')
            # Look for common magic terms
            magic_keywords = ['saidin', 'saidar', 'one power', 'channeling', 'weave',
                            'angreal', 'ter\'angreal', 'sa\'angreal', 'talent', 'ability']
            for keyword in magic_keywords:
                if keyword in content.lower():
                    related_terms.add(keyword.title())
        
        # Extract character mentions
        all_content = ' '.join(s.get('content', '') for s in sections)
        related_characters = self.extract_character_mentions(all_content)
        
        return {
            'category': category,
            'description': description,
            'related_terms': sorted(list(related_terms)),
            'related_characters': related_characters[:10],  # Top 10 to avoid clutter
            'source_file': filename,
            'full_sections': sections  # Keep for reference
        }
    
    def process_all(self):
        """Process all prophecy and magic pages."""
        print("\n" + "="*80)
        print("PROPHECY & MAGIC SYSTEM EXTRACTOR - Week 3 Goal 4")
        print("="*80)
        
        # Load concepts
        concepts_file = self.config.FILE_WIKI_CONCEPT
        print(f"\n📂 Loading concepts from: {concepts_file}")
        
        with open(concepts_file, 'r', encoding='utf-8') as f:
            concepts = json.load(f)
        
        print(f"✓ Loaded {len(concepts)} concept pages")
        
        # Process prophecy pages
        print("\n🔮 Processing prophecy pages...")
        prophecy_index = {}
        
        for filename in self.prophecy_pages:
            if filename not in concepts:
                print(f"  ⚠️  {filename} not found in concepts")
                continue
            
            page_data = concepts[filename]
            page_name = page_data.get('page_name', filename.replace('.txt', ''))
            
            prophecy_data = self.extract_prophecy_data(page_data)
            prophecy_index[page_name] = prophecy_data
            
            print(f"  ✓ {page_name}")
            print(f"      Type: {prophecy_data['type']}")
            print(f"      Practitioners: {len(prophecy_data['practitioners'])}")
            print(f"      Related characters: {len(prophecy_data['related_characters'])}")
        
        # Process magic system pages
        print("\n✨ Processing magic system pages...")
        magic_index = {}
        
        for filename in self.magic_pages:
            if filename not in concepts:
                print(f"  ⚠️  {filename} not found in concepts")
                continue
            
            page_data = concepts[filename]
            page_name = page_data.get('page_name', filename.replace('.txt', ''))
            
            magic_data = self.extract_magic_data(page_data)
            magic_index[page_name] = magic_data
            
            print(f"  ✓ {page_name} ({magic_data['category']})")
        
        # Save prophecy index
        prophecy_output = self.config.FILE_PROPHECY_INDEX
        print(f"\n💾 Saving prophecy index to: {prophecy_output}")
        prophecy_output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(prophecy_output, 'w', encoding='utf-8') as f:
            json.dump(prophecy_index, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(prophecy_index)} prophecy entries")
        
        # Save magic system index
        magic_output = self.config.FILE_MAGIC_SYSTEM_INDEX
        print(f"\n💾 Saving magic system index to: {magic_output}")
        
        with open(magic_output, 'w', encoding='utf-8') as f:
            json.dump(magic_index, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(magic_index)} magic system entries")
        
        # Statistics
        self.print_statistics(prophecy_index, magic_index)
    
    def print_statistics(self, prophecy_index: Dict, magic_index: Dict):
        """Print extraction statistics."""
        print("\n" + "="*80)
        print("EXTRACTION STATISTICS")
        print("="*80)
        
        print(f"\n📊 Prophecy Index:")
        print(f"  Total entries: {len(prophecy_index)}")
        
        # Group by type
        types = {}
        for entry in prophecy_index.values():
            ptype = entry['type']
            types[ptype] = types.get(ptype, 0) + 1
        
        for ptype, count in types.items():
            print(f"    {ptype}: {count}")
        
        total_practitioners = sum(len(e['practitioners']) for e in prophecy_index.values())
        print(f"  Total practitioners listed: {total_practitioners}")
        
        print(f"\n📊 Magic System Index:")
        print(f"  Total entries: {len(magic_index)}")
        
        # Group by category
        categories = {}
        for entry in magic_index.values():
            cat = entry['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            print(f"    {cat}: {count}")
        
        print("\n" + "="*80)


def main():
    """Main execution."""
    extractor = ProphecyMagicExtractor()
    extractor.process_all()
    
    print("\n✅ Prophecy & Magic extraction complete!")
    print("\n📁 Output files:")
    config = get_config()
    print(f"  Prophecy: {config.FILE_PROPHECY_INDEX}")
    print(f"  Magic: {config.FILE_MAGIC_SYSTEM_INDEX}")


if __name__ == "__main__":
    main()