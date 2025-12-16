"""Check actual structure of index files"""

import json
from pathlib import Path

# Assume standard paths
base_path = Path("C:/Users/victor.diaz/Documents/_AI/dragon-codex")
metadata_path = base_path / "data" / "metadata"

print("=" * 70)
print("CHECKING INDEX FILE STRUCTURES")
print("=" * 70)

# Character Index
char_index_file = metadata_path / "wiki" / "character_index.json"
if char_index_file.exists():
    print("\n📄 CHARACTER INDEX STRUCTURE:")
    with open(char_index_file, "r") as f:
        char_index = json.load(f)

    # Get first few entries
    sample_chars = list(char_index.items())[:3]
    for name, data in sample_chars:
        print(f"\n  Character: {name}")
        print(f"    Keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
        if isinstance(data, dict):
            if "aliases" in data:
                print(f"    Aliases: {data['aliases'][:3] if isinstance(data['aliases'], list) else data['aliases']}")
            if "titles" in data:
                print(f"    Titles: {data['titles'][:2] if isinstance(data['titles'], list) else data['titles']}")
else:
    print("\n⚠️  Character index not found at expected location")

# Magic Index
magic_index_file = metadata_path / "wiki" / "magic_system_index.json"
if magic_index_file.exists():
    print("\n📄 MAGIC SYSTEM INDEX STRUCTURE:")
    with open(magic_index_file, "r") as f:
        magic_index = json.load(f)

    sample_magic = list(magic_index.items())[:2]
    for name, data in sample_magic:
        print(f"\n  Term: {name}")
        print(f"    Keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
        if isinstance(data, dict) and "related_terms" in data:
            print(f"    Related: {data['related_terms'][:3] if isinstance(data['related_terms'], list) else data['related_terms']}")
else:
    print("\n⚠️  Magic index not found at expected location")

# Concept Index
concept_index_file = metadata_path / "wiki" / "concept_index.json"
if concept_index_file.exists():
    print("\n📄 CONCEPT INDEX STRUCTURE:")
    with open(concept_index_file, "r") as f:
        concept_index = json.load(f)

    sample_concepts = list(concept_index.items())[:2]
    for name, data in sample_concepts:
        print(f"\n  Concept: {name}")
        print(f"    Keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
else:
    print("\n⚠️  Concept index not found at expected location")

print("\n" + "=" * 70)
