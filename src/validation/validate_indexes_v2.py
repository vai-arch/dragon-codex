"""
Dragon's Codex - Index Validation Script
Validates character, magic, and prophecy indexes (v2.0 - category-based)

Checks:
- Character Index: Major characters have expected fields, categories properly extracted
- Magic Index: Categories classified correctly, types assigned
- Prophecy Index: Types identified, aliases present
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

from config import Config

config = Config()

# Major characters to validate (the big 5 + a few others)
MAJOR_CHARACTERS = [
    "Rand al'Thor",
    "Mat Cauthon", 
    "Perrin Aybara",
    "Egwene al'Vere",
    "Elayne Trakand",
    "Nynaeve al'Meara",
    "Moiraine Damodred",
    "Lan Mandragoran"
]

# Expected magic pages
EXPECTED_MAGIC_PAGES = [
    "One Power",
    "Angreal",
    "Sa'angreal",
    "Ter'angreal",
    "Saidin",
    "Channeling"
]

# Expected prophecy pages
EXPECTED_PROPHECY_PAGES = [
    "Karaethon Cycle",
    "Foretelling",
    "Min's viewings"
]


class IndexValidator:
    """Validates all v2 indexes."""
    
    def __init__(self):
        """Initialize validator."""
        self.character_index = None
        self.magic_index = None
        self.prophecy_index = None
        self.issues = []
    
    def load_indexes(self):
        """Load all indexes."""
        print("\n📂 Loading indexes...")
        
        # Character index
        char_path = config.FILE_CHARACTER_INDEX
        if not char_path.exists():
            self.issues.append(f"CHARACTER INDEX NOT FOUND: {char_path}")
            return False
        
        with open(char_path, 'r', encoding='utf-8') as f:
            self.character_index = json.load(f)
        print(f"   ✓ Character index: {len(self.character_index):,} characters")
        
        # Magic index
        magic_path = config.FILE_MAGIC_SYSTEM_INDEX
        if not magic_path.exists():
            self.issues.append(f"MAGIC INDEX NOT FOUND: {magic_path}")
            return False
        
        with open(magic_path, 'r', encoding='utf-8') as f:
            self.magic_index = json.load(f)
        print(f"   ✓ Magic index: {len(self.magic_index):,} pages")
        
        # Prophecy index
        prophecy_path = config.FILE_PROPHECY_INDEX
        if not prophecy_path.exists():
            self.issues.append(f"PROPHECY INDEX NOT FOUND: {prophecy_path}")
            return False
        
        with open(prophecy_path, 'r', encoding='utf-8') as f:
            self.prophecy_index = json.load(f)
        print(f"   ✓ Prophecy index: {len(self.prophecy_index):,} pages")
        
        return True
    
    def validate_character_index(self):
        """Validate character index structure and major characters."""
        print("\n" + "="*80)
        print("VALIDATING CHARACTER INDEX")
        print("="*80)
        
        if not self.character_index:
            self.issues.append("Character index not loaded")
            return
        
        # Statistics
        stats = {
            'total': len(self.character_index),
            'with_gender': 0,
            'with_channeling': 0,
            'with_aliases': 0,
            'with_nationalities': 0,
            'with_special_abilities': 0,
        }
        
        for name, data in self.character_index.items():
            if data.get('gender'):
                stats['with_gender'] += 1
            if data.get('can_channel'):
                stats['with_channeling'] += 1
            if data.get('aliases'):
                stats['with_aliases'] += 1
            if data.get('nationalities'):
                stats['with_nationalities'] += 1
            if data.get('special_abilities'):
                stats['with_special_abilities'] += 1
        
        print(f"\n📊 Character Index Statistics:")
        print(f"   Total characters:           {stats['total']:6,}")
        print(f"   With gender:                {stats['with_gender']:6,} ({stats['with_gender']/stats['total']*100:5.1f}%)")
        print(f"   With channeling:            {stats['with_channeling']:6,} ({stats['with_channeling']/stats['total']*100:5.1f}%)")
        print(f"   With aliases:               {stats['with_aliases']:6,} ({stats['with_aliases']/stats['total']*100:5.1f}%)")
        print(f"   With nationalities:         {stats['with_nationalities']:6,} ({stats['with_nationalities']/stats['total']*100:5.1f}%)")
        print(f"   With special abilities:     {stats['with_special_abilities']:6,} ({stats['with_special_abilities']/stats['total']*100:5.1f}%)")
        
        # Validate major characters
        print(f"\n🔍 Validating Major Characters:")
        
        for char_name in MAJOR_CHARACTERS:
            print(f"\n   {char_name}:")
            
            if char_name not in self.character_index:
                self.issues.append(f"MISSING: {char_name} not in character index")
                print(f"      ❌ NOT FOUND IN INDEX")
                continue
            
            char = self.character_index[char_name]
            
            # Check essential fields
            if not char.get('gender'):
                self.issues.append(f"{char_name}: Missing gender")
                print(f"      ⚠️  No gender")
            else:
                print(f"      ✓ Gender: {char['gender']}")
            
            if not char.get('aliases'):
                self.issues.append(f"{char_name}: No aliases found")
                print(f"      ⚠️  No aliases")
            else:
                print(f"      ✓ Aliases: {len(char['aliases'])} found")
            
            if char.get('can_channel'):
                print(f"      ✓ Channeling: {char.get('channeling_type', 'unknown')}")
                if char.get('channeling_affiliations'):
                    print(f"         Affiliations: {', '.join(char['channeling_affiliations'])}")
            
            if char.get('special_abilities'):
                print(f"      ✓ Special abilities: {', '.join(char['special_abilities'])}")
            
            if char.get('nationalities'):
                print(f"      ✓ Nationality: {', '.join(char['nationalities'])}")
    
    def validate_magic_index(self):
        """Validate magic index structure and classifications."""
        print("\n" + "="*80)
        print("VALIDATING MAGIC INDEX")
        print("="*80)
        
        if not self.magic_index:
            self.issues.append("Magic index not loaded")
            return
        
        # Statistics by type
        type_counts = defaultdict(int)
        stats = {
            'total': len(self.magic_index),
            'with_aliases': 0,
            'with_description': 0,
            'with_object_type': 0,
        }
        
        for name, data in self.magic_index.items():
            magic_type = data.get('type', 'unknown')
            type_counts[magic_type] += 1
            
            if data.get('aliases'):
                stats['with_aliases'] += 1
            if data.get('description'):
                stats['with_description'] += 1
            if data.get('object_type'):
                stats['with_object_type'] += 1
        
        print(f"\n📊 Magic Index Statistics:")
        print(f"   Total magic pages:          {stats['total']:6,}")
        print(f"   With aliases:               {stats['with_aliases']:6,} ({stats['with_aliases']/stats['total']*100:5.1f}%)")
        print(f"   With descriptions:          {stats['with_description']:6,} ({stats['with_description']/stats['total']*100:5.1f}%)")
        print(f"   With object_type:           {stats['with_object_type']:6,}")
        
        print(f"\n   By Type:")
        for magic_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"      {magic_type:20s} {count:6,}")
        
        # Validate expected pages
        print(f"\n🔍 Validating Expected Magic Pages:")
        
        for page_name in EXPECTED_MAGIC_PAGES:
            print(f"\n   {page_name}:")
            
            if page_name not in self.magic_index:
                self.issues.append(f"MISSING: {page_name} not in magic index")
                print(f"      ❌ NOT FOUND IN INDEX")
                continue
            
            page = self.magic_index[page_name]
            
            print(f"      ✓ Type: {page.get('type', 'unknown')}")
            
            if page.get('object_type'):
                print(f"      ✓ Object type: {page['object_type']}")
            
            if page.get('aliases'):
                print(f"      ✓ Aliases: {len(page['aliases'])} found")
            
            if page.get('description'):
                desc_preview = page['description'][:80] + "..." if len(page['description']) > 80 else page['description']
                print(f"      ✓ Description: {desc_preview}")
    
    def validate_prophecy_index(self):
        """Validate prophecy index structure and types."""
        print("\n" + "="*80)
        print("VALIDATING PROPHECY INDEX")
        print("="*80)
        
        if not self.prophecy_index:
            self.issues.append("Prophecy index not loaded")
            return
        
        # Statistics by type
        type_counts = defaultdict(int)
        stats = {
            'total': len(self.prophecy_index),
            'with_aliases': 0,
            'with_description': 0,
        }
        
        for name, data in self.prophecy_index.items():
            prophecy_type = data.get('type', 'unknown')
            type_counts[prophecy_type] += 1
            
            if data.get('aliases'):
                stats['with_aliases'] += 1
            if data.get('description'):
                stats['with_description'] += 1
        
        print(f"\n📊 Prophecy Index Statistics:")
        print(f"   Total prophecy pages:       {stats['total']:6,}")
        print(f"   With aliases:               {stats['with_aliases']:6,} ({stats['with_aliases']/stats['total']*100:5.1f}%)")
        print(f"   With descriptions:          {stats['with_description']:6,} ({stats['with_description']/stats['total']*100:5.1f}%)")
        
        print(f"\n   By Type:")
        for prophecy_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"      {prophecy_type:20s} {count:6,}")
        
        # Validate expected pages
        print(f"\n🔍 Validating Expected Prophecy Pages:")
        
        for page_name in EXPECTED_PROPHECY_PAGES:
            print(f"\n   {page_name}:")
            
            if page_name not in self.prophecy_index:
                self.issues.append(f"MISSING: {page_name} not in prophecy index")
                print(f"      ❌ NOT FOUND IN INDEX")
                continue
            
            page = self.prophecy_index[page_name]
            
            print(f"      ✓ Type: {page.get('type', 'unknown')}")
            
            if page.get('aliases'):
                print(f"      ✓ Aliases: {len(page['aliases'])} found")
            
            if page.get('description'):
                desc_preview = page['description'][:80] + "..." if len(page['description']) > 80 else page['description']
                print(f"      ✓ Description: {desc_preview}")
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        if not self.issues:
            print("\n✅ ALL VALIDATIONS PASSED!")
            print("   No issues found. Indexes are ready for Week 5.")
        else:
            print(f"\n⚠️  FOUND {len(self.issues)} ISSUES:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
            print("\n   Please review and fix issues before proceeding to Week 5.")
        
        print("\n" + "="*80)


def main():
    """Main validation function."""
    
    print("\n" + "="*80)
    print("DRAGON'S CODEX - INDEX VALIDATION (v2.0)")
    print("="*80)
    
    validator = IndexValidator()
    
    # Load indexes
    if not validator.load_indexes():
        print("\n❌ Failed to load indexes. Cannot proceed with validation.")
        return
    
    # Validate each index
    validator.validate_character_index()
    validator.validate_magic_index()
    validator.validate_prophecy_index()
    
    # Print summary
    validator.print_summary()


if __name__ == "__main__":
    main()
