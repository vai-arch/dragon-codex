import os
import pickle

from src.utils.paths import get_paths

paths = get_paths()
file_path = paths.FILE_WIKI_CHARACTER_EMBEDDINGS  # Adjust if needed

# First, check file size
print(f"File size: {os.path.getsize(file_path) / (1024 * 1024):.2f} MB")
with open(file_path, "rb") as f:
    data = pickle.load(f)

print("\nType of loaded object:", type(data))
print("Number of chunks:", len(data))
print("Example keys:", list(data.keys())[:10])  # First 10 chunk IDs

# Inspect a few chunks in detail
for i, key in enumerate(list(data.keys())[:5]):  # Show first 5 chunks
    chunk_dict = data[key]
    print(f"\n--- Chunk {i} ('{key}') ---")
    print("Inner dict keys:", list(chunk_dict.keys()))
    for sub_key, sub_value in chunk_dict.items():
        print(f" - {sub_key}:")
        print(f"     Type: {type(sub_value)}")
        if hasattr(sub_value, "shape"):  # Likely numpy array for embedding
            print(f"     Shape: {sub_value.shape}")
            print(f"     Dtype: {sub_value.dtype}")
            print(f"     Preview (first 10 values): {sub_value.flatten()[:10]}")
        elif isinstance(sub_value, str):
            print(f"     Length: {len(sub_value)}")
            print(f"     Preview: {sub_value[:300]}...")  # First 300 chars of text
        elif isinstance(sub_value, list):
            print(f"     Length: {len(sub_value)}")
            print(f"     Preview: {sub_value[:5]}")
        else:
            print(f"     Value preview: {sub_value}")
