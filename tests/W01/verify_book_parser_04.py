import json

# Load New Spring (prequel, book 00)
with open('data/raw/books/00-New_Spring.json', 'r', encoding='utf-8') as f:
    new_spring = json.load(f)

print("Edge Case: New Spring (Prequel)")
print("="*70)
print(f"Book number: {new_spring['book_number']} (should be '00')")
print(f"Chapter count: {len(new_spring['chapters'])}")
print(f"Glossary count: {len(new_spring['glossary'])}")

# Check it parsed correctly
if new_spring['book_number'] == '00':
    print("✓ Prequel book number correct")
else:
    print("✗ Prequel book number wrong!")

# Load A Memory of Light (last book, longest)
with open('data/raw/books/14-A_Memory_of_Light.json', 'r', encoding='utf-8') as f:
    amol = json.load(f)

print("\nEdge Case: A Memory of Light (Last book)")
print("="*70)
print(f"Book number: {amol['book_number']} (should be '14')")
print(f"Chapter count: {len(amol['chapters'])} (longest book)")
print(f"Glossary count: {len(amol['glossary'])}")

# Check epilogue handling
epilogues = [ch for ch in amol['chapters'] if ch['type'] == 'epilogue']
if epilogues:
    print(f"\n✓ Epilogue found:")
    print(f"  Number: {epilogues[0]['number']}")
    print(f"  Title: {epilogues[0]['title']}")
else:
    print("\n⚠ No epilogue found (some books may not have one)")