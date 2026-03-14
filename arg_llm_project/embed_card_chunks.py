import json
import numpy as np
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load CARD chunks
with open("data/card_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

texts = [chunk["text"] for chunk in chunks]

print(f"Loaded {len(texts)} chunks")

# Create embeddings
embeddings = model.encode(texts, show_progress_bar=True)

print("Embeddings shape:", embeddings.shape)  # (N, 384)

# Save embeddings + metadata
output = []
for i, chunk in enumerate(chunks):
    output.append({
        "chunk_id": chunk["chunk_id"],
        "gene_name": chunk["gene_name"],
        "aro_id": chunk["aro_id"],
        "text": chunk["text"],
        "embedding": embeddings[i].tolist()
    })

with open("data/card_embeddings.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("Saved embeddings to data/card_embeddings.json")
