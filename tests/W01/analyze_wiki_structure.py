import json
import glob
import re
from pathlib import Path
from collections import Counter

def analyze_wiki_files():
    """Analyze structure of scraped wiki files"""
    
    wiki_dir = Path('data/raw/wiki_complete')
    
    # Alternative path if you moved them
    if not wiki_dir.exists():
        wiki_dir = Path('data/raw/wiki')
    
    if not wiki_dir.exists():
        print("✗ Wiki directory not found!")
        print("  Expected: data/raw/wiki_complete or data/raw/wiki")
        return
    
    wiki_files = list(wiki_dir.glob('*.txt'))
    
    print("="*70)
    print("WIKI FILES STRUCTURE ANALYSIS")
    print("="*70)
    print(f"\nTotal wiki files: {len(wiki_files):,}\n")
    
    # Sample 100 random files for analysis
    import random
    sample_size = min(100, len(wiki_files))
    sample_files = random.sample(wiki_files, sample_size)
    
    # Track patterns
    has_infobox = 0
    has_categories = 0
    temporal_sections_count = []
    non_temporal_sections_count = []
    all_temporal_books = []
    all_non_temporal_sections = []
    
    print(f"Analyzing {sample_size} random files...\n")
    
    for wiki_file in sample_files:
        with open(wiki_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for infobox
        if '## Information' in content or '## Character Information' in content:
            has_infobox += 1
        
        # Check for categories
        if '## Categories' in content or '<!-- Categories:' in content:
            has_categories += 1
        
        # Find temporal sections (## In [Book Name])
        temporal_sections = re.findall(r'##\s+In\s+(.+?)(?=\n)', content)
        temporal_sections_count.append(len(temporal_sections))
        all_temporal_books.extend(temporal_sections)
        
        # Find all H2 sections
        all_h2 = re.findall(r'##\s+(.+?)(?=\n)', content)
        non_temporal = [s for s in all_h2 if not s.startswith('In ') 
                       and s not in ['Information', 'Character Information', 'Categories']]
        non_temporal_sections_count.append(len(non_temporal))
        all_non_temporal_sections.extend(non_temporal)
    
    # Results
    print("STRUCTURAL FEATURES:")
    print("-"*70)
    print(f"Files with Infobox:           {has_infobox:3}/{sample_size} ({has_infobox/sample_size*100:.1f}%)")
    print(f"Files with Categories:        {has_categories:3}/{sample_size} ({has_categories/sample_size*100:.1f}%)")
    
    print("\nTEMPORAL SECTIONS (## In [Book Name]):")
    print("-"*70)
    avg_temporal = sum(temporal_sections_count) / len(temporal_sections_count)
    print(f"Average temporal sections:    {avg_temporal:.1f} per file")
    print(f"Max temporal sections:        {max(temporal_sections_count)}")
    print(f"Files with temporal sections: {sum(1 for x in temporal_sections_count if x > 0)}/{sample_size}")
    
    # Most common book titles in temporal sections
    book_counter = Counter(all_temporal_books)
    print(f"\nMost common temporal section titles:")
    for book, count in book_counter.most_common(10):
        print(f"  In {book}: {count} occurrences")
    
    print("\nNON-TEMPORAL SECTIONS:")
    print("-"*70)
    avg_non_temporal = sum(non_temporal_sections_count) / len(non_temporal_sections_count)
    print(f"Average non-temporal sections: {avg_non_temporal:.1f} per file")
    
    # Most common non-temporal sections
    section_counter = Counter(all_non_temporal_sections)
    print(f"\nMost common non-temporal sections:")
    for section, count in section_counter.most_common(15):
        print(f"  {section}: {count} occurrences")
    
    # Save results
    output_file = Path('data/metadata/wiki_structure_analysis.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        'total_files_analyzed': sample_size,
        'total_files_in_directory': len(wiki_files),
        'has_infobox_percent': has_infobox / sample_size * 100,
        'has_categories_percent': has_categories / sample_size * 100,
        'avg_temporal_sections': avg_temporal,
        'avg_non_temporal_sections': avg_non_temporal,
        'common_temporal_books': dict(book_counter.most_common(15)),
        'common_non_temporal_sections': dict(section_counter.most_common(15))
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    analyze_wiki_files()