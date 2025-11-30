import json

# Load one book
with open('data/raw/books/01-The_Eye_of_the_World.json', 'r', encoding='utf-8') as f:
    book1 = json.load(f)

print("="*70)
print(f"Book: {book1['book_name']}")
print("="*70)

# Check first 3 chapters
for i, chapter in enumerate(book1['chapters'][:3]):
    print(f"\n{chapter['type'].upper()} {chapter['number']}: {chapter['title']}")
    print(f"Content length: {len(chapter['content'])} characters")
    print(f"First 200 chars: {chapter['content'][:200]}...")
    
    # Verify content is not empty
    if len(chapter['content']) < 100:
        print("⚠ WARNING: Chapter content seems too short!")

# Check last chapter
if book1['chapters']:
    last = book1['chapters'][-1]
    print(f"\n{last['type'].upper()} {last['number']}: {last['title']}")
    print(f"Content length: {len(last['content'])} characters")

# Check glossary
print("\n" + "="*70)
print(f"GLOSSARY ({len(book1['glossary'])} entries)")
print("="*70)

for i, entry in enumerate(book1['glossary'][:5], 1):
    print(f"\n{i}. {entry['term']}")
    if entry['pronunciation']:
        print(f"   Pronunciation: {entry['pronunciation']}")
    print(f"   Description: {entry['description'][:100]}...")