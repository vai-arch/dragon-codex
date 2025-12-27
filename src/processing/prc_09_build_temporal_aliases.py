import re
import sys
import traceback
from datetime import datetime
from difflib import SequenceMatcher
from multiprocessing import Pool, cpu_count

from tqdm import tqdm

from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file, load_json_line_by_line, save_json_to_file
from src.utils.util_statistics import total_statistics_logging

in_file_redirect_aliases_mapping = None
in_file_book_chunks = None
in_file_character_index = None
out_file_temporal_aliases = None


def process_chunks(chunks, alias_regex):
    local_result = {}

    for chunk in chunks:
        text = chunk["text"].lower()
        book_num = chunk["book_number"]

        for match in alias_regex.finditer(text):
            alias = match.group(1).lower()

            if alias not in local_result or book_num < local_result[alias]:
                local_result[alias] = book_num

    return local_result


def chunkify(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def is_obvious_variant(canonical: str, alias: str) -> bool:
    # Normalize both
    can_lower = canonical.lower()
    alias_lower = alias.lower().replace("(", "").replace(")", "")

    # Cleaned versions (remove apostrophes/spaces/hyphens for strict matching)
    can_clean = can_lower.replace("'", "").replace(" ", "").replace("-", "")
    alias_clean = alias_lower.replace("'", "").replace(" ", "").replace("-", "")

    # Rule 1: Exact match ignoring case/punctuation/spaces
    if can_clean == alias_clean:
        return True

    # Rule 2: Alias is significant substring (>70%)
    if alias_clean in can_clean and len(alias_clean) / len(can_clean) > 0.7:
        return True

    # Rule 3: Reordered words match (sorted word list)
    can_words = sorted(re.split(r"[\s'\-\.]", can_lower))
    alias_words = sorted(re.split(r"[\s'\-\.]", alias_lower))
    if can_words and alias_words and can_words == alias_words:
        return True

    # Rule 4: High Levenshtein similarity
    similarity = SequenceMatcher(None, can_clean, alias_clean).ratio()
    if similarity > 0.85:
        return True

    # Rule 5: First name exact match (e.g., "aeldrine" → "Aeldrine Marinye")
    first_name_can = re.split(r"[\s']", can_lower)[0]
    first_name_alias = re.split(r"[\s']", alias_lower)[0]
    if first_name_can == first_name_alias:
        return True

    # Rule 6: Single word in canonical (short forms)
    if len(alias_lower.split()) == 1 and alias_lower in can_lower:
        return True

    # NEW Rule 7: Comma-reversed surname-first format (e.g., "al'vere, egwene")
    if "," in alias_lower:
        parts = [p.strip() for p in alias_lower.split(",", 1)]
        if len(parts) == 2:
            surname, firstname = parts
            # Reconstruct expected canonical order: firstname + surname
            expected = f"{firstname} {surname}"
            expected_clean = expected.replace("'", "").replace(" ", "")
            if expected_clean in can_clean or can_clean in expected_clean:
                return True
            # Also check if words match regardless of order
            if sorted([firstname, surname]) == sorted(re.split(r"[\s']", can_lower)):
                return True

    # Rule 8: Common WoT suffixes (sedai, din, ti) with prefix match
    if any(suf in alias_lower for suf in ["sedai", "din", "ti", "lord", "lady"]):
        prefix = can_lower.split()[0].replace("'", "")
        if alias_lower.startswith(prefix):
            return True

    return False


def main():
    start_time = datetime.now()

    canonical_to_aliases = load_json_from_file(in_file_redirect_aliases_mapping)

    alias_to_canonical = {}
    for canonical, aliases in canonical_to_aliases.items():
        for a in aliases:
            alias_to_canonical[a.lower()] = canonical

    temporal_aliases = {
        alias: {
            "canonical": canonical,
            "first_seen_book": float("inf"),
        }
        for alias, canonical in alias_to_canonical.items()
    }

    # ADD CANONICAL SELF-ENTRIES
    for canonical in canonical_to_aliases.keys():
        can_lower = canonical.lower()
        if can_lower not in alias_to_canonical:
            temporal_aliases[canonical] = {
                "canonical": canonical,
                "first_seen_book": float("inf"),
                "is_obvious_variant": False,
            }

    # NO BLACKLIST — Use all keys
    escaped_aliases = sorted(
        (re.escape(k) for k in temporal_aliases.keys()),
        key=len,
        reverse=True,
    )

    alias_regex = re.compile(
        r"\b(" + "|".join(escaped_aliases) + r")\b",
        re.IGNORECASE,
    )

    books_chunks = list(load_json_line_by_line(in_file_book_chunks))

    num_aliases_in_no_books = 0
    num_aliases_in_books = 0
    num_obvious_variants = 0

    num_workers = max(1, cpu_count() - 1)
    batch_size = max(1, len(books_chunks) // (num_workers * 4))
    batches = list(chunkify(books_chunks, batch_size))

    with Pool(num_workers) as pool:
        results = list(
            tqdm(
                pool.starmap(process_chunks, [(b, alias_regex) for b in batches]),
                total=len(batches),
                desc="Processing chunks (parallel)",
            )
        )

    # Reduce step - normalized lookup
    for partial in results:
        for alias_original, book_num in partial.items():
            alias_lower = alias_original.lower()
            if alias_lower in temporal_aliases:
                entry = temporal_aliases[alias_lower]
                if book_num < entry["first_seen_book"]:
                    entry["first_seen_book"] = book_num

    # Cleanup & Stats
    for alias_key, data in temporal_aliases.items():
        if data["first_seen_book"] == float("inf"):
            data["first_seen_book"] = None
            num_aliases_in_no_books += 1
            data["source"] = "wiki_only"

            if data["canonical"].lower() != alias_key.lower():
                obvious = is_obvious_variant(data["canonical"], alias_key)
                data["is_obvious_variant"] = obvious
                num_obvious_variants += int(obvious)
            else:
                data["is_obvious_variant"] = False
        else:
            num_aliases_in_books += 1
            data["is_obvious_variant"] = False

    save_json_to_file(temporal_aliases, out_file_temporal_aliases, indent=2)

    statistics = {
        "name": "temporal_aliases",
        "metrics": {
            "aliases_in_books": num_aliases_in_books,
            "aliases_in_no_books": num_aliases_in_no_books,
            "num_obvious_variants": num_obvious_variants,
            "total_canonicals_added": len(canonical_to_aliases),
            "total_aliases_processed": len(temporal_aliases),
        },
    }

    total_time = datetime.now() - start_time
    total_statistics_logging(total_time=total_time, log_name="prc_09_build_temporal_aliases", statistics=statistics, title="TEMPORAL ALIASES (auto-canonicals, no blacklist)", tables=False)


if __name__ == "__main__":
    paths = get_paths()

    in_file_redirect_aliases_mapping = paths.FILE_REDIRECT_ALIASES_MAPPING
    in_file_book_chunks = paths.FILE_BOOK_CHUNKS
    in_file_character_index = paths.FILE_CHARACTER_INDEX
    out_file_temporal_aliases = paths.FILE_TEMPORAL_ALIASES

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
