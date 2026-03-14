import json
import numpy as np
import faiss

# Load embeddings
with open("data/card_embeddings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

embeddings = np.array([item["embedding"] for item in data]).astype("float32")

dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)

index.add(embeddings)

# Save index
faiss.write_index(index, "data/card_faiss.index")

print(f"FAISS index built with {index.ntotal} vectors")
