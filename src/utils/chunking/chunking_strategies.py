import re
from typing import List

from scipy.spatial.distance import cosine

from src.utils.config import get_embedding_manager_config
from src.utils.embedding.embedding_factory import create_embedding_manager

# Global model - loaded once
_embedding_manager = None


def _get_embedding_manager():
    global _embedding_manager
    if _embedding_manager is None:
        from src.utils.config import get_config

        config = get_config()
        _embedding_manager = create_embedding_manager(config.EMBEDDING_MANAGER, get_embedding_manager_config(config.EMBEDDING_MANAGER))
    return _embedding_manager


def split_text_semantic(text: str, target_tokens: int = 1000, min_tokens: int = 600, overlap_tokens: int = 200, similarity_bonus_threshold: float = 0.82) -> List[str]:
    """
    Size-driven chunking with light semantic protection.
    Fully compatible with embedding_manager returning tuple (embeddings, count).
    """
    if not text.strip():
        return []

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"“])', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    # Early returns for short text — no embedding needed
    if len(sentences) == 0:
        return []
    if len(sentences) <= 5:
        return [text.strip()]

    # Get embeddings via manager (no prefix for internal similarity)
    embedding_manager = _get_embedding_manager()  # Assuming global or injectable
    embed_result = embedding_manager.embed_chunks(
        texts=sentences,
        show_progress=False,
        prefix=embedding_manager.get_manager_config()["EMBEDDING_MODEL"]["EMBEDDING_MODEL_RAW_PREFIX"],
    )

    # Safe extraction of embeddings
    if isinstance(embed_result, (tuple, list)):
        embeddings_raw = embed_result[0]
    else:
        embeddings_raw = embed_result

    import numpy as np

    embeddings = np.array(embeddings_raw)

    if embeddings.ndim != 2 or embeddings.shape[0] != len(sentences):
        return [text.strip()]  # Fallback to whole block

    chunks = []
    i = 0
    while i < len(sentences):
        current_sents = []
        current_tokens = 0
        start_i = i

        while i < len(sentences):
            next_sent_tokens = len(sentences[i].split())
            if current_tokens + next_sent_tokens > target_tokens + 50:
                break

            # Semantic guard
            if current_tokens > min_tokens and len(current_sents) > 0 and i > start_i and 1 - cosine(embeddings[i - 1], embeddings[i]) < (1 - similarity_bonus_threshold):
                break

            current_sents.append(sentences[i])
            current_tokens += next_sent_tokens
            i += 1

        if not current_sents:
            current_sents = sentences[start_i:]
            i = len(sentences)

        chunk_text = " ".join(current_sents)
        chunks.append(chunk_text)

        # Overlap
        if overlap_tokens > 0 and i < len(sentences):
            words_so_far = 0
            overlap_count = 0
            for sent in reversed(current_sents):
                words_so_far += len(sent.split())
                overlap_count += 1
                if words_so_far >= overlap_tokens:
                    break
            if overlap_count > 0:
                rewind_to = len(sentences) - len(current_sents) + overlap_count
                i = max(i, rewind_to)

    return chunks


def hybrid_chunker(text: str, wiki_type: str) -> List[str]:
    """
    Hybrid chunking for wiki pages:
    - Structural: Split by markdown headings first.
    - Semantic: Refine long sections with split_text_semantic.

    Args:
        text: Raw wiki page content (markdown)
        wiki_type: 'character', 'chapter_summary', 'chronology', or 'concept'

    Returns:
        List of chunk strings (ready for metadata addition)
    """
    from src.utils.config import get_config

    config = get_config().CHUNKING_STRATEGY

    # Load type-specific config (fallback to defaults if not implemented)
    min_section_size = config[f"WIKI_{wiki_type.upper()}_MIN_SECTION_SIZE"]
    similarity_threshold = config[f"WIKI_{wiki_type.upper()}_SEMANTIC_THRESHOLD"]
    target_tokens = config["SEMANTIC_MAX_CHUNK_TOKENS"]
    min_tokens = target_tokens // 2
    overlap_tokens = config["SEMANTIC_OVERLAP_TOKENS"]

    # 1. Structural split: Extract heading + content blocks
    sections = re.split(r"(^#{2,6}\s.+?$)", text, flags=re.MULTILINE)
    blocks = []
    current_heading = ""
    current_content = []
    for part in sections:
        if part.strip().startswith("#"):
            if current_content:
                blocks.append(f"{current_heading}\n\n{' '.join(current_content)}")
            current_heading = part.strip()
            current_content = []
        else:
            if part.strip():
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"“])', part.strip())
                current_content.extend([s.strip() for s in sentences if s.strip()])
    if current_content:
        blocks.append(f"{current_heading}\n\n{' '.join(current_content)}")

    # 2. Process each block
    chunks = []
    for block in blocks:
        # Keep short sections whole (e.g., short bios or definitions)
        if len(block) < min_section_size:
            chunks.append(block)
            continue

        # Apply semantic chunking to long sections
        sub_chunks = split_text_semantic(text=block, target_tokens=target_tokens, min_tokens=min_tokens, overlap_tokens=overlap_tokens, similarity_bonus_threshold=similarity_threshold)
        chunks.extend(sub_chunks)

    return chunks


def get_chunker(strategy: str, wiki_type: str = None):
    """
    Factory returning the appropriate chunking pipeline.
    """
    from src.utils.config import get_config

    config = get_config()

    if strategy == "legacy":
        from src.utils.chunking.util_chunking_functions import (
            split_into_paragraphs,
            split_paragraph_into_chunks,
        )

        def legacy_chunker(text: str) -> List[str]:
            paragraphs = split_into_paragraphs(text)
            chunks = []
            for para in paragraphs:
                chunks.extend(split_paragraph_into_chunks(para))
            return chunks

        return legacy_chunker

    elif strategy == "semantic":

        def semantic_chunker(text: str) -> List[str]:
            return split_text_semantic(
                text=text,
                target_tokens=config.CHUNKING_STRATEGY["SEMANTIC_MAX_CHUNK_TOKENS"],  # ← maps old max to new target
                min_tokens=config.CHUNKING_STRATEGY["SEMANTIC_MAX_CHUNK_TOKENS"] // 2,  # ← optional: sensible default (e.g., 500 if max=1000)
                overlap_tokens=config.CHUNKING_STRATEGY["SEMANTIC_OVERLAP_TOKENS"],
                similarity_bonus_threshold=config.CHUNKING_STRATEGY["SEMANTIC_SIMILARITY_THRESHOLD"],  # ← rename intent
            )

        return semantic_chunker

    elif strategy == "hybrid":

        def hybrid_wrapper(text: str) -> List[str]:
            if wiki_type is None:
                raise ValueError("hybrid_chunker requires wiki_type")
            return hybrid_chunker(text, wiki_type)

        return hybrid_wrapper

    else:
        raise ValueError(f"Unknown strategy: {strategy}")
