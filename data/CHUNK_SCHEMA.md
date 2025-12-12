
# Dragon's Codex - Unified Chunk Schema

## Version 1.0 - Week 4 Final

---

## Common Fields (All Chunks)

All chunks, regardless of source, contain these fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `source` | string | Source type: "book" or "wiki" | "book" |
| `text` | string | Chunk content | "Rand stood atop..." |
| `temporal_order` | int or null | Book number (0-14) for temporal content, null for non-temporal | 3 |
| `character_mentions` | array[string] | Canonical character names mentioned | ["Rand al'Thor", "Moiraine"] |
| `concept_mentions` | array[string] | WoT concept terms mentioned | ["Aes Sedai", "One Power"] |
| `magic_mentions` | array[string] | Magic system terms mentioned | ["Channeling", "Saidin"] |

---

## Book Chunk Fields

Additional fields for chunks with `source: "book"`:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `chunk_id` | string | Unique chunk identifier | "book_03_ch_05_chunk_002" |
| `book_number` | int | Book number (0-14) | 3 |
| `book_title` | string | Book title | "The Dragon Reborn" |
| `chapter_number` | int | Chapter number | 5 |
| `chapter_title` | string | Chapter title | "Nightmares Walking" |
| `chapter_type` | string | Type: "prologue", "chapter", "epilogue" | "chapter" |
| `chunk_index` | int | Chunk number within chapter | 2 |
| `total_chunks_in_chapter` | int | Total chunks in this chapter | 5 |

---

## Wiki Chunk Fields

Additional fields for chunks with `source: "wiki"`:

### Common Wiki Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `wiki_type` | string | Type: "chronology", "character", "chapter_summary", "concept" | "character" |
| `filename` | string | Original wiki filename | "Rand_al'Thor.txt" |

### Type-Specific Fields

**Chronology chunks:**
- `character_name`: string
- `book_number`: int
- `book_title`: string

**Character chunks:**
- `character_name`: string
- `section_title`: string

**Chapter Summary chunks:**
- `book_number`: int
- `book_title`: string
- `chapter_number`: int
- `chapter_title`: string
- `chunk_part`: string or null (e.g., "1 of 3" if split)

**Concept chunks:**
- `concept_name`: string
- `section_title`: string
- `chunk_part`: string or null (e.g., "1 of 2" if split)

---

## Metadata Enrichment

All chunks have been enriched with three types of mentions:

1. **Character Mentions**: Extracted using character index with 2,450 characters and 3,063 name variations
2. **Concept Mentions**: Extracted using unified glossary with 496 WoT-specific terms
3. **Magic Mentions**: Extracted using magic system index with 40 magic-related concepts

All mention arrays use canonical names and are sorted alphabetically.

---

## Temporal Organization

Chunks are organized temporally using `temporal_order`:
- **Book 0**: New Spring (prequel)
- **Books 1-14**: Main series in reading order
- **null**: Non-temporal content (reference material, character bios, etc.)

This enables spoiler-free querying: "up to book 5" filters to `temporal_order <= 5`.

---

## Size Constraints

All chunks adhere to these limits:
- **Target**: ~1000 tokens (~4000 characters)
- **Maximum**: 2000 tokens (~8000 characters)
- **Splitting**: Large sections split at paragraph boundaries with semantic coherence

---

## Data Quality

- ✅ 24,773 total chunks validated
- ✅ All chunks have required fields
- ✅ All temporal orders valid (0-14 or null)
- ✅ All chunks under 2000 token limit
- ✅ Character mentions: 69,996 instances
- ✅ Concept mentions: 77,716 instances
- ✅ Magic mentions: 4,495 instances

---

## Usage Notes

**For Retrieval:**
- Use `temporal_order` to filter by reading progress
- Use `character_mentions` to find all mentions of a character
- Use `concept_mentions` for WoT terminology queries
- Use `magic_mentions` for magic system queries
- Use `source` and `wiki_type` to route queries to appropriate content

**For Context Assembly:**
- Book chunks include chapter context for continuity
- Wiki chunks include section titles for structure
- Temporal ordering enables chronological assembly
- Mention arrays enable entity-focused retrieval
