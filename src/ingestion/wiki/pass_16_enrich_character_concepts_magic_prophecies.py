import sys
import ahocorasick
import re
from pathlib import Path
from typing import Set
from tqdm import tqdm
from src.utils.config import get_config
from src.utils.util_files_functions import load_json_from_file, save_jsonl_to_file, load_line_by_line
from src.utils.util_statistics import log_results, log_results_table, print_results

class ConceptMagicProphecyTagger:
    """Tag chunks with WoT concepts, magic system, and prophecy mentions."""

    def __init__(self):
        """Initialize with indexes and AC automatons."""
        self.character_terms = {}  # {lowercase_term: original_term}
        self.concept_terms = {}
        self.magic_terms = {}
        self.prophecy_terms = {}

        self.ac_characters = None
        self.ac_concepts = None
        self.ac_magic = None
        self.ac_prophecy = None

        self._load_indexes()

    def build_ac_automaton(self, terms_dict):
        """Build an Aho-Corasick automaton from a dict of lowercase -> original terms."""
        A = ahocorasick.Automaton()
        for term_lower, original in terms_dict.items():
            term_normalized = f" {term_lower.strip()} "
            A.add_word(term_normalized, original)
        A.make_automaton()
        return A

    def normalize_text_for_ac(self, text: str) -> str:
        """Normalize text for AC: lowercase, replace punctuation, pad with spaces."""
        import string
        text_lower = text.lower()
        text_clean = re.sub(f"[{re.escape(string.punctuation)}]", " ", text_lower)
        text_padded = f" {text_clean} "
        return text_padded

    def _load_indexes(self):
        """Load all indexes and build Aho–Corasick automatons."""
        config = get_config()

        # Helper to load a JSON index and normalize
        def load_index(file_path):
            index = load_json_from_file(file_path)
            terms = {}
            for page_name, data in index.items():
                terms[page_name.lower()] = page_name
                for alias in data.get("aliases", []):
                    terms[alias.lower()] = page_name
            return terms, index

        self.character_terms, char_index = load_index(config.FILE_CHARACTER_INDEX)
        self.concept_terms, concept_index = load_index(config.FILE_CONCEPT_INDEX)
        self.magic_terms, magic_index = load_index(config.FILE_MAGIC_SYSTEM_INDEX)
        self.prophecy_terms, prophecy_index = load_index(config.FILE_PROPHECY_INDEX)

        print(f"✓ Loaded {len(char_index)} characters ({len(self.character_terms)} with aliases)")
        print(f"✓ Loaded {len(concept_index)} concepts ({len(self.concept_terms)} with aliases)")
        print(f"✓ Loaded {len(magic_index)} magic ({len(self.magic_terms)} with aliases)")
        print(f"✓ Loaded {len(prophecy_index)} prophecies ({len(self.prophecy_terms)} with aliases)")

        # Build AC automatons
        self.ac_characters = self.build_ac_automaton(self.character_terms)
        self.ac_concepts = self.build_ac_automaton(self.concept_terms)
        self.ac_magic = self.build_ac_automaton(self.magic_terms)
        self.ac_prophecy = self.build_ac_automaton(self.prophecy_terms)

    def extract_mentions(self, text: str, automaton, topic_name: str = None) -> list:
        """
        Extract mentions from text using Aho-Corasick automaton.
        Also adds topic_name if it exactly matches a term in the automaton.

        Args:
            text: The text to search (string).
            automaton: Aho-Corasick automaton containing all terms.
            topic_name: Optional topic name (string) to ensure exact match.

        Returns:
            Sorted list of found mentions.
        """
        # Normalize text for AC search
        text_norm = f" {text.lower()} "
        found = set()

        # AC scanning for all terms
        for _, original in automaton.iter(text_norm):
            found.add(original)

        # Add topic_name only if it is present in the automaton
        if topic_name:
            topic_name_lower = topic_name.lower()
            if topic_name_lower in (term.lower() for term in automaton.values()):
                found.add(topic_name)

        return sorted(found)


    def enrich_chunk_file(self, file_path: Path, chunk_type: str):
        """Add mentions to all chunks in a JSONL file."""
        print(f"\n📂 Processing {chunk_type} ({file_path.name})")
        chunks = load_line_by_line(file_path)

        # Counters
        counters = {
            "characters": 0, "concepts": 0, "magic": 0, "prophecies": 0,
            "total_characters": 0, "total_concepts": 0, "total_magic": 0, "total_prophecies": 0
        }

        pbar = tqdm(chunks, desc="Processing chunks", dynamic_ncols=True, leave=False, file=sys.stderr)
        for chunk in pbar:
            text = chunk.get("text", "")
            page_name = chunk.get("page_name", "")
            character_name = chunk.get("character_name", "")
            topic_name = page_name or character_name or ""

            topic_name = chunk.get("page_name") or chunk.get("character_name")
            character_mentions = self.extract_mentions(text, self.ac_characters, topic_name)
            concept_mentions   = self.extract_mentions(text, self.ac_concepts, topic_name)
            magic_mentions     = self.extract_mentions(text, self.ac_magic, topic_name)
            prophecy_mentions  = self.extract_mentions(text, self.ac_prophecy, topic_name)

            # Update chunk
            chunk["character_mentions"] = character_mentions
            chunk["concept_mentions"] = concept_mentions
            chunk["magic_mentions"] = magic_mentions
            chunk["prophecy_mentions"] = prophecy_mentions

            # Update counters
            counters["characters"] += int(bool(character_mentions))
            counters["concepts"] += int(bool(concept_mentions))
            counters["magic"] += int(bool(magic_mentions))
            counters["prophecies"] += int(bool(prophecy_mentions))
            counters["total_characters"] += len(character_mentions)
            counters["total_concepts"] += len(concept_mentions)
            counters["total_magic"] += len(magic_mentions)
            counters["total_prophecies"] += len(prophecy_mentions)

            pbar.set_postfix_str(
                f"Characters: {counters['characters']}, Concepts: {counters['concepts']}, "
                f"Magic: {counters['magic']}, Prophecies: {counters['prophecies']}"
            )

        save_jsonl_to_file(chunks, file_path)
        print(f"   ✅ Enriched {len(chunks):,} chunks")
        return counters

# Main execution
def main():
    config = get_config()

    print("=" * 80)
    print("CONCEPT, MAGIC & PROPHECY TAGGING - Week 4 Goal 4 (v2.0)")
    print("=" * 80)

    tagger = ConceptMagicProphecyTagger()

    chunk_files = [
        (config.FILE_BOOK_CHUNKS, "Books"),
        (config.FILE_WIKI_CHUNKS_CHAPTER_SUMMARY, "Wiki Chapter Summary"),
        (config.FILE_WIKI_CHUNKS_CHRONOLOGY, "Wiki Chronology"),
        (config.FILE_WIKI_CHUNKS_CHARACTER, "Wiki Character"),
        (config.FILE_WIKI_CHUNKS_CONCEPT, "Wiki Concept"),
        (config.FILE_WIKI_CHUNKS_MAGIC, "Wiki Magic"),
        (config.FILE_WIKI_CHUNKS_PROPHECIES, "Wiki Prophecy"),
    ]

    results = {}
    for file_path, chunk_type in chunk_files:
        if not file_path.exists():
            print(f"⚠️  Warning: {file_path.name} not found, skipping")
            continue
        results[chunk_type] = tagger.enrich_chunk_file(file_path, chunk_type)

    resultados = []
    for chunk_type, stats in results.items():

        total_chunks = max(stats.get('characters',0),
                        stats.get('concepts',0),
                        stats.get('magic',0),
                        stats.get('prophecies',0))
        if total_chunks == 0:
            total_chunks = 1
        resultado = {
            "name": chunk_type,
            "metrics": {
                "Characters": (stats.get('characters', 0), stats.get('characters',0)/total_chunks*100),
                "Concepts": (stats.get('concepts', 0), stats.get('concepts',0)/total_chunks*100),
                "Magic": (stats.get('magic', 0), stats.get('magic',0)/total_chunks*100),
                "Prophecies": (stats.get('prophecies', 0), stats.get('prophecies',0)/total_chunks*100),
                "Total Chunks": total_chunks
            }
        }

        resultados.append(resultado)
    
    print_results(resultados, "CHUNK ENRICHMENT STATISTICS")
    log_results(resultados, "chunk_enrichment", "CHUNK ENRICHMENT STATISTICS")
    log_results_table(resultados, "chunk_enrichment", "CHUNK ENRICHMENT STATISTICS")

if __name__ == "__main__":
    main()
