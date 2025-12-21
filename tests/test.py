# Test your model
from torch import cosine_similarity

embedder = SentenceTransformerEmbedder("C:\\Users\\Usuario\\Documents\\_AI\\codex-forge\\models\\finetuned")

# Embed two IDENTICAL texts
emb1 = embedder.embed(["The Trollocs charged"])[0]
emb2 = embedder.embed(["The Trollocs charged"])[0]

# Calculate similarity
similarity = cosine_similarity(emb1, emb2)
print(f"Self-similarity: {similarity}")
