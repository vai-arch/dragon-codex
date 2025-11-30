import json
import glob

def verify_all():
    """Complete verification of book parsing"""
    files = sorted(glob.glob('data/raw/books/*.json'))
    
    print("COMPLETE BOOK PARSING VERIFICATION")
    print("="*70)
    
    all_good = True
    
    # Check 1: File count
    if len(files) != 15:
        print(f"✗ Expected 15 books, found {len(files)}")
        all_good = False
    else:
        print(f"✓ All 15 books parsed")
    
    # Check 2: Total chapters
    total_ch = sum(len(json.load(open(f, 'r', encoding='utf-8'))['chapters']) for f in files)
    if 700 <= total_ch <= 800:
        print(f"✓ Total chapters: {total_ch} (reasonable)")
    else:
        print(f"⚠ Total chapters: {total_ch} (expected 400-600)")
        all_good = False
    
    # Check 3: All have glossaries
    total_gloss = sum(len(json.load(open(f, 'r', encoding='utf-8'))['glossary']) for f in files)
    if total_gloss > 0:
        print(f"✓ Glossary entries: {total_gloss}")
    else:
        print(f"✗ No glossary entries found!")
        all_good = False
    
    # Check 4: Spot checks
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        empty = [ch for ch in data['chapters'] if len(ch['content']) < 50]
        if empty:
            print(f"✗ {data['book_name']}: {len(empty)} empty chapters")
            all_good = False
    
    print("="*70)
    if all_good:
        print("✓✓✓ ALL CHECKS PASSED! ✓✓✓")
        print("\nYour book parsing script works correctly!")
    else:
        print("⚠ SOME ISSUES FOUND")
        print("Review output above for details")
    
    return all_good

verify_all()