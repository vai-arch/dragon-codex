import json
import glob
from pathlib import Path

# Get all JSON outputs
json_files = sorted(glob.glob('data/raw/books/*.json'))

print("Book Parsing Verification")
print("="*70)

total_books = 0
total_chapters = 0
total_glossary = 0

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    book_num = data['book_number']
    book_name = data['book_name']
    chapter_count = len(data['chapters'])
    glossary_count = len(data['glossary'])
    
    # Count chapter types
    prologues = sum(1 for ch in data['chapters'] if ch['type'] == 'prologue')
    regular = sum(1 for ch in data['chapters'] if ch['type'] == 'chapter')
    epilogues = sum(1 for ch in data['chapters'] if ch['type'] == 'epilogue')
    
    print(f"{book_num} - {book_name[:35]:35} | "
          f"Total: {chapter_count:3} (P:{prologues} + C:{regular:2} + E:{epilogues}) | "
          f"Glossary: {glossary_count:3}")
    
    total_books += 1
    total_chapters += chapter_count
    total_glossary += glossary_count

print("="*70)
print(f"TOTALS: {total_books} books | {total_chapters} chapters | {total_glossary} glossary terms")
print("="*70)

# Expected: 400-500 total chapters
if 400 <= total_chapters <= 600:
    print("✓ Chapter count looks reasonable!")
else:
    print(f"⚠ Chapter count ({total_chapters}) outside expected range 400-600")

# Expected: 200-400 unique glossary terms (may have duplicates across books)
if total_glossary > 0:
    print(f"✓ Glossary parsed ({total_glossary} total entries across all books)")
else:
    print("✗ No glossary entries found!")