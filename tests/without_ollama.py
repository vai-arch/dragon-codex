# import ollama
# from sentence_transformers import SentenceTransformer

# from src.utils.config import Config

# # Test text
# text = "The Wheel of Time turns"

# # Ollama embedding
# ollama_emb = ollama.embed(model=Config().EMBEDDING_MODEL, input=text)['embeddings'][0]

# # SentenceTransformer embedding
# model = SentenceTransformer('nomic-ai/nomic-embed-text-v1.5', trust_remote_code=True)
# st_emb = model.encode(text)

# # Compare
# import numpy as np
# cosine_sim = np.dot(ollama_emb, st_emb) / (np.linalg.norm(ollama_emb) * np.linalg.norm(st_emb))
# print(f"Cosine similarity: {cosine_sim}")  # Should be > 0.99 if compatible



import requests
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from numpy.linalg import norm

# --------------------------------------------------
# Define the input text and model versions
# --------------------------------------------------
# Use the exact same text input for both methods.
# The 'search_query: ' prefix is recommended for Nomic models when embedding a query.
input_text = "search_query: How do I use the latest Nomic model?"

# --------------------------------------------------
# 1. Get embedding from SentenceTransformer (Official PyTorch implementation)
# --------------------------------------------------
st_model_name = "nomic-ai/nomic-embed-text-v1.5"
st_model = SentenceTransformer(st_model_name, trust_remote_code=True)
st_embedding = st_model.encode(input_text )
print(f"ST embedding shape: {st_embedding.shape}")

# --------------------------------------------------
# 2. Get embedding from Ollama API (llama.cpp GGUF implementation)
# --------------------------------------------------
ollama_url = "http://localhost:11434/api/embeddings"
ollama_payload = {
    "model": "nomic-embed-text",  # This pulls the default v1.5 version
    "prompt": input_text
}

# The Ollama API returns pre-normalized vectors by default
response = requests.post(ollama_url, data=json.dumps(ollama_payload))
response_data = response.json()
ollama_embedding = np.array(response_data['embedding'])
print(f"Ollama embedding shape: {ollama_embedding.shape}")

# --------------------------------------------------
# 3. Calculate Cosine Similarity
# --------------------------------------------------

def cosine_similarity(A, B):
    # Ensure inputs are numpy arrays
    A = np.array(A)
    B = np.array(B)
    
    # Cosine sim is dot product divided by the product of the L2 norms
    # If both inputs are already normalized (L2 norm of 1), this simplifies to A.dot(B)
    return np.dot(A, B) / (norm(A) * norm(B))

# Calculate similarity
# Note: Since both ST and Ollama return normalized vectors by default, 
# the similarity should be very high if the models are truly identical.
similarity_score = cosine_similarity(st_embedding, ollama_embedding)

print("-" * 40)
print(f"Cosine similarity between ST and Ollama embeddings: {similarity_score}")
