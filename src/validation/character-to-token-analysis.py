import requests
from src.utils.util_embedding import EmbeddingManager

from src.utils.config import get_config
from src.utils.util_files_functions import find_files_in_folder, load_json_from_file

config = get_config()
manager = EmbeddingManager()


def get_token_count(content):
    chunks = []
    chunks.append(content)
    result = manager.embed_chunks(chunks, 1)
    return result[1]
    # print(f"chaper length {len(content)} tokens: {result[1]}")


def get_actual_token_count(text, model=config.EMBEDDING_MODEL):
    """
    Get actual token count from Ollama.
    We'll use the generate API which might give us token info,
    or we'll need to check what Ollama actually returns.
    """
    try:
        # Try the generate endpoint to see token info
        response = requests.post(f"{config.OLLAMA_BASE_URL}/api/generate", json={"model": model, "prompt": text, "stream": False}, timeout=30)

        if response.status_code == 200:
            result = response.json()
            # Print what we get back to see the structure
            return result
        else:
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


# Get first book
json_files_paths = find_files_in_folder(config.AUXILIARY_BOOKS_PATH, ".json")
book_data = load_json_from_file(json_files_paths[0], False)

print(f"Book: {book_data.get('title', 'Unknown')}")
print(f"Total chapters: {len(book_data.get('chapters', []))}")
print()

# Test with first chapter to see what Ollama returns
first_chapter = book_data.get("chapters", [])[2]
content = first_chapter["content"]

print(f"Testing chapter: {first_chapter.get('chapter_number', 'Unknown')}")
print(f"Character count: {len(content)}")
print()
print("Calling Ollama to get actual token count...")
print()

print("Finding actual character-to-token ratio and truncation point:")
print("=" * 60)
print(config.MAX_CHUNK_SIZE)
print(config.CHUNK_SIZE)

# Test increasing character counts to find where truncation happens
test_sizes = [1000, 2000, 4000, 6000, 8000, 10000]
for size in test_sizes:
    if size <= len(content):
        test_text = content[:size]
        tokens = get_token_count(test_text)
        ratio = size / tokens if tokens else 0
        print(f"Chars: {size:5d} | Tokens: {tokens} | Ratio: {ratio:.2f} | Truncated: {'YES' if tokens >= 2046 else 'NO'}")
