import json
import glob

json_files = sorted(glob.glob('data/raw/books/*.json'))

print("Checking for parsing issues...")
print("="*70)

issues_found = []

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    book_name = data['book_name']
    
    # Check 1: Any chapters with empty content?
    empty_chapters = [ch for ch in data['chapters'] if len(ch['content']) < 50]
    if empty_chapters:
        issues_found.append(f"{book_name}: {len(empty_chapters)} chapters with < 50 chars")
    
    # Check 2: Any chapters with empty titles?
    no_title = [ch for ch in data['chapters'] if not ch['title']]
    if no_title:
        issues_found.append(f"{book_name}: {len(no_title)} chapters with no title")
    
    # Check 3: Chapter numbers sequential?
    regular_chapters = [ch for ch in data['chapters'] if ch['type'] == 'chapter']
    if regular_chapters:
        numbers = [ch['number'] for ch in regular_chapters]
        expected = list(range(1, len(regular_chapters) + 1))
        if numbers != expected:
            issues_found.append(f"{book_name}: Chapter numbers not sequential: {numbers[:10]}...")
    
    # Check 4: Duplicate chapter numbers?
    all_numbers = [ch['number'] for ch in data['chapters']]
    if len(all_numbers) != len(set(all_numbers)):
        issues_found.append(f"{book_name}: Duplicate chapter numbers detected")
    
    # Check 5: Glossary entries have descriptions?
    no_desc = [g for g in data['glossary'] if not g.get('description', '').strip()]
    if no_desc:
        issues_found.append(f"{book_name}: {len(no_desc)} glossary entries with no description")

if issues_found:
    print("⚠ ISSUES FOUND:\n")
    for issue in issues_found:
        print(f"  - {issue}")
else:
    print("✓ No issues found!")
    print("\nAll books parsed correctly:")
    print("  ✓ All chapters have content")
    print("  ✓ All chapters have titles")
    print("  ✓ Chapter numbers are sequential")
    print("  ✓ No duplicate chapter numbers")
    print("  ✓ All glossary entries have descriptions")

print("="*70)