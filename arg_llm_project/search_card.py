import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load FAISS index
index = faiss.read_index("data/card_faiss.index")

# Load metadata
with open("data/card_embeddings.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

def search(query, k=3):
    q_emb = model.encode([query]).astype("float32")
    distances, indices = index.search(q_emb, k)

    results = []
    for idx in indices[0]:
        results.append(metadata[idx])

    return results

# Test query
query_text = "beta lactamase gene resistance mechanism"
results = search(query_text)

for r in results:
    print("\nGene:", r["gene_name"])
    print("ARO:", r["aro_id"])
    print("Text:", r["text"])
