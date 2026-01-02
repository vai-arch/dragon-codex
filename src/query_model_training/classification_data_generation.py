import random
import sys
import traceback

from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file, load_json_line_by_line, save_jsonl_to_file

# Initialize paths and config
paths = get_paths()
config = get_config()

# Paths to indexes
INDEX_PATHS = {
    "character": paths.FILE_CHARACTER_INDEX,
    "prophecy": paths.FILE_PROPHECY_INDEX,
    "magic_system": paths.FILE_MAGIC_SYSTEM_INDEX,
    "concept": paths.FILE_WIKI_CONCEPT,
    "timeline": paths.FILE_TIMELINE_INDEX,  # New: Dedicated timeline index
}

# Output
FILE_AUTOMATICALLY_GENERATED_QUESTIONS = paths.FILE_QUERY_CLASSIFIER_MODEL_TRAINING_DATA_AUTOMATIC
FILE_MANUALLY_GENERATED_QUESTIONS = paths.FILE_QUERY_CLASSIFIER_MODEL_TRAINING_DATA_MANUAL
FILE_ALL_GENERATED_QUESTIONS = paths.FILE_QUERY_CLASSIFIER_MODEL_TRAINING_DATA_ALL


# Base category for each index
BASE_CATEGORY = {
    "character": "character",
    "prophecy": "prophecy",
    "magic_system": "magic_system",
    "concept": "concept",
    "timeline": "timeline",
}

# Sub-type overrides (from "type" field or categories)
SUBTYPE_MAP = {
    "historical": "timeline",
    "battle": "timeline",
    "war": "timeline",
    "date_year": "timeline",
    "era": "timeline",
    "item": "concept",
    "location": "concept",
    "organization": "concept",
    "cultural": "concept",
    "creature": "concept",
    "power_object": "magic_system",
    "is_weave": "magic_system",
}

# Templates per category
TEMPLATES = {
    "character": [
        "Who is {name}?",
        "Tell me about {name} in the Wheel of Time",
        "Describe {name}'s background and role",
        "What nationality is {name} from?",
        "How is {name} connected to {organization}?",
    ],
    "prophecy": [
        "What does the {name} prophecy foretell?",
        "Explain the meaning of {name}",
        "How was {name} fulfilled in the series?",
        "Describe the {type} known as {alias}",
        "What is the significance of {description_snippet}?",
    ],
    "magic_system": [
        "What is {name} ({object_type})?",
        "Explain how {name} functions with the One Power",
        "Describe the effects of {name}",
        "How is {name} used in channeling?",
        "What makes {name} dangerous or special?",
    ],
    "concept": [
        "What is {name} in the Wheel of Time?",
        "Describe {name} ({type})",
        "Explain the role of {name}",
        "What is known about {name} from {categories}?",
        "How does {name} impact the story?",
    ],
    "timeline": [
        "What happened during {name}?",
        "List the major events in {name}",
        "What is the significance of {name} in the timeline?",
        "Describe the key events of {name}",
        "When did the events of {name} occur?",
        "Summarize the timeline for {name}",
    ],
}

# Multi-label cross templates
MULTI_TEMPLATES = [
    "How does {name1} relate to {name2}?",
    "Describe {name1}'s role in {name2}",
    "What happened to {name1} during {name2}?",
    "How is {name1} involved in the events of {name2}?",
    "Explain {name1}'s connection to {name2} in the timeline",
]


def main():
    data = {}
    for cat, path in INDEX_PATHS.items():
        if not path.exists():
            raise FileNotFoundError(f"Index not found: {path}")
        data[cat] = load_json_from_file(path)

    automatic_queries = []
    seen = set()

    for cat, entries in data.items():
        base_cat = BASE_CATEGORY[cat]
        for key, entry in entries.items():
            # Extract name
            name = entry.get("primary_name") or entry.get("name") or entry.get("page_name", key)
            aliases = entry.get("aliases", [])
            all_names = [name] + aliases[:2]

            # Determine categories
            entry_type = entry.get("type", "").lower()
            sub_cat = SUBTYPE_MAP.get(entry_type, base_cat)

            # Additional category detection
            categories = [sub_cat]
            if entry.get("power_related") or entry.get("is_weave") or entry.get("object_type"):
                categories.append("magic_system")
            if any(word in entry_type for word in ["historical", "battle", "war", "date", "era"]):
                categories.append("timeline")
            if "prophecy" in entry_type or "foretelling" in entry_type:
                categories.append("prophecy")

            categories = list(set(categories))

            # Generate base queries
            templates = TEMPLATES.get(sub_cat, TEMPLATES["concept"])
            num_queries = random.randint(4, 8)
            for _ in range(num_queries):
                template = random.choice(templates)
                text = template.format(
                    name=random.choice(all_names),
                    alias=random.choice(aliases) if aliases else name,
                    type=entry.get("type", ""),
                    object_type=entry.get("object_type", ""),
                    description_snippet=(entry.get("description") or entry.get("overview") or "")[:60],
                    categories=", ".join(entry.get("categories", [])[:2]),
                    organization=random.choice(entry.get("organizations", ["the story"])),
                    nationality=random.choice(entry.get("nationalities", ["the Westlands"])),
                )

                # Variations
                if random.random() < 0.4:
                    text = text.replace("What is", "Explain").replace("Who is", "Tell me about")
                if random.random() < 0.2:
                    text += f" up to book {random.randint(1, 14)}"

                query_key = (text, tuple(sorted(categories)))
                if query_key not in seen:
                    seen.add(query_key)
                    automatic_queries.append({"text": text, "categories": categories})
                    automatic_queries.append({"text": text, "categories": categories})

            # Multi-label cross-index (25% chance)
            if random.random() < 0.25 and len(data) > 1:
                other_cat = random.choice([c for c in data if c != cat])
                other_entry = random.choice(list(data[other_cat].values()))
                other_name = other_entry.get("primary_name") or other_entry.get("name") or other_entry.get("page_name", "unknown")
                text = random.choice(MULTI_TEMPLATES).format(
                    name1=name,
                    name2=other_name,
                )
                multi_cats = list(set(categories + [BASE_CATEGORY[other_cat]]))
                query_key = (text, tuple(sorted(multi_cats)))
                if query_key not in seen:
                    seen.add(query_key)
                    automatic_queries.append({"text": text, "categories": multi_cats})

        # Shuffle auto-generated queries
    random.shuffle(automatic_queries)

    # Save automatically generated
    save_jsonl_to_file(data=automatic_queries, output_file=FILE_AUTOMATICALLY_GENERATED_QUESTIONS, indent=None)
    print(f"Generated and saved {len(automatic_queries)} automatic queries → {FILE_AUTOMATICALLY_GENERATED_QUESTIONS}")

    # Load manually generated queries and standardize format
    print(f"Loading manual queries from {FILE_MANUALLY_GENERATED_QUESTIONS}...")
    manual_raw = load_json_line_by_line(FILE_MANUALLY_GENERATED_QUESTIONS)

    manual_queries = []
    for item in manual_raw:
        # Standardize: ensure "text" and "categories" keys, with text first
        text = item.get("text") or item.get("question", "")
        categories = item.get("categories") or item.get("category", [])
        if isinstance(categories, str):
            categories = [categories]

        standardized = {"text": text.strip(), "categories": categories}
        manual_queries.append(standardized)

    print(f"Loaded and standardized {len(manual_queries)} manual queries")

    # Optional: Re-save manual in new standardized format (for consistency)
    save_jsonl_to_file(data=manual_queries, output_file=FILE_MANUALLY_GENERATED_QUESTIONS, indent=None)
    print(f"Re-saved standardized manual queries → {FILE_MANUALLY_GENERATED_QUESTIONS}")

    # Combine manual + automatic
    total_queries = manual_queries + automatic_queries
    random.shuffle(total_queries)

    # Deduplicate total
    seen = set()
    unique_total = []
    for q in total_queries:
        key = (q["text"], tuple(sorted(q["categories"])))
        if key not in seen:
            seen.add(key)
            unique_total.append(q)

    # Save total
    save_jsonl_to_file(data=unique_total, output_file=FILE_ALL_GENERATED_QUESTIONS, indent=None)
    print(f"Saved {len(unique_total)} total unique queries (manual + auto) → {FILE_ALL_GENERATED_QUESTIONS}")

    print("\nQuery generation complete!")
    print(f"   • Manual:     {len(manual_queries)}")
    print(f"   • Automatic:  {len(automatic_queries)}")
    print(f"   • Total:      {len(unique_total)}")


if __name__ == "__main__":
    try:
        main()
        exit_code = 0
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)
