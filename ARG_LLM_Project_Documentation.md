# ARG-LLM Project Documentation
## Antibiotic Resistance Gene Identification using RAG + LLM

---

##  Project Overview

This project builds an AI-powered system that can identify and explain **Antibiotic Resistance Genes (ARGs)** from genomic sequence data. It combines:

- **DIAMOND** — a fast sequence alignment tool to detect ARGs in sample sequences
- **CARD Database** — a curated knowledge base of antibiotic resistance genes
- **RAG (Retrieval-Augmented Generation)** — a technique that gives an LLM access to a structured knowledge base so it can answer domain-specific questions accurately
- **FAISS** — a vector similarity search library used as the AI's "memory"
- **Sentence Transformers** — to convert text into numerical vector embeddings
- **LLM** — to reason over retrieved gene information and generate meaningful answers

---

##  Core Concept: What is RAG?

> **RAG = Retrieval-Augmented Generation**

Instead of relying only on an LLM's pre-trained knowledge (which may be outdated or limited), RAG lets the model **retrieve relevant documents from a database** before generating an answer.

```
User Query
    │
    ▼
[Embedding Model] ──► Convert query to a vector
    │
    ▼
[FAISS Index] ──► Find most similar knowledge chunks
    │
    ▼
[Retrieved Text Chunks] ──► Passed to LLM as context
    │
    ▼
[LLM] ──► Generates a grounded, accurate answer
```

This approach ensures the LLM answers based on **real, curated ARG knowledge** rather than hallucinating.

---

##  Data Sources

| File | Description |
|------|-------------|
| `card.json` | Full CARD database dump — contains ARO entries, gene names, descriptions, mechanisms |
| `protein_fasta_protein_homolog_model.fasta` | Protein sequences from CARD used to build the DIAMOND database |
| `nucleotide_fasta_protein_homolog_model.fasta` | Nucleotide sequences (alternative input for DIAMOND) |
| `sample.fasta` | Input genomic sample to be analyzed |

---

##  Full Pipeline — Step by Step

### Step 1 — Project Setup

```bash
mkdir arg_llm_project
cd arg_llm_project

python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install torch transformers sentence-transformers faiss-cpu chromadb pandas numpy scikit-learn
```

Creates an isolated Python environment and installs all required libraries.

---

### Step 2 — Build DIAMOND Database

```bash
diamond makedb --in protein_fasta_protein_homolog_model.fasta -d card_db
```

**What it does:**
- Takes the CARD protein sequences (FASTA format)
- Compiles them into a binary DIAMOND database (`card_db.dmnd`)
- This database is used for fast protein-level sequence alignment

**Why DIAMOND?**
DIAMOND is up to 20,000× faster than BLAST for protein sequence alignment while maintaining comparable accuracy.

---

### Step 3 — Run Sequence Alignment

```bash
diamond blastx -d card_db -q sample.fasta -o result.tsv
```

**What it does:**
- Takes your input genomic sample (`sample.fasta`)
- Translates DNA into all 6 reading frames (blastx mode)
- Aligns translated sequences against the CARD protein database
- Outputs a tab-separated results file (`result.tsv`) with matched ARGs

**Output columns include:** query ID, subject (gene) ID, % identity, alignment length, E-value, bit score

---

### Step 4 — Parse CARD Database (`parse_card.py`)

**Input:** `data/card.json`  
**Output:** `data/card_extracted.json`

```python
# Extracts for each ARG entry:
{
  "gene_name": "...",
  "aro_id": "...",
  "description": "...",
  "mechanism": "..."
}
```

**What it does:**
- Loads the full CARD JSON database (~6000+ entries)
- Filters out metadata and non-gene entries (keeps only those with `ARO_accession`)
- Extracts key fields: gene name, ARO ID, description, and resistance mechanism

---

### Step 5 — Chunk the Text (`chunk_card.py`)

**Input:** `data/card_extracted.json`  
**Output:** `data/card_chunks.json`

**Why chunking?**
Embedding models have a token limit (typically 256–512 tokens). Long descriptions must be split into smaller **chunks** so each piece fits within the model's input window and carries focused meaning.

**What it does:**
- Combines description + mechanism into a single text per gene
- Splits text into **150-word chunks**
- Labels each chunk with a unique ID (`{aro_id}_{chunk_index}`)

```json
{
  "chunk_id": "3000026_0",
  "gene_name": "NDM-1",
  "aro_id": "3000026",
  "text": "NDM-1 is a metallo-beta-lactamase that confers resistance..."
}
```

---

### Step 6 — Generate Embeddings (`embed_card_chunks.py`)

**Input:** `data/card_chunks.json`  
**Output:** `data/card_embeddings.json`

**What is an Embedding?**
An embedding is a **numerical vector** (list of numbers) that represents the semantic meaning of a text. Similar texts produce similar vectors (close in vector space).

```
"NDM-1 beta-lactamase" → [0.12, -0.45, 0.88, ..., 0.03]  (384 dimensions)
```

**What it does:**
- Loads the `all-MiniLM-L6-v2` sentence transformer model (lightweight, fast, 384-dim vectors)
- Encodes every text chunk into a 384-dimensional vector
- Saves the embeddings alongside metadata

---

### Step 7 — Build FAISS Index (`build_faiss_index.py`)

**Input:** `data/card_embeddings.json`  
**Output:** `data/card_faiss.index`

**What is FAISS?**
> **FAISS (Facebook AI Similarity Search)** is a library for **fast similarity search over large collections of vectors**.

Given a query vector → FAISS finds the **most similar vectors** in the index (nearest neighbors).

```
Query Vector ──► [FAISS IndexFlatL2] ──► Top-K most similar chunk vectors
```

Uses **L2 (Euclidean) distance** to measure similarity between vectors.

**What it does:**
- Loads all 384-dim embedding vectors
- Adds them into a `IndexFlatL2` FAISS index (exact search)
- Saves the index to disk for reuse

>  **Think of FAISS as the AI's long-term memory** — it lets the system instantly recall the most relevant ARG knowledge for any query.

---

### Step 8 — Search the Index (`search_card.py`)

**What it does:**
- Accepts a natural language query (e.g., *"beta-lactamase gene resistance mechanism"*)
- Embeds the query using the same `all-MiniLM-L6-v2` model
- Searches the FAISS index for top-K (default: 3) most similar chunks
- Returns matching gene names, ARO IDs, and text passages

```python
results = search("beta lactamase gene resistance mechanism", k=3)
# Returns top 3 most semantically relevant chunks from CARD
```

---

### Step 9 — LLM Reasoning (`llm_reasoning.py`)

**What it does (planned):**
- Takes the retrieved CARD chunks as context
- Passes them along with the user's query to an LLM
- The LLM synthesizes a meaningful, grounded answer about the ARG

This is the final **RAG** step — connecting retrieval to generation.

---

##  Complete Data Flow Diagram

```
protein_fasta_protein_homolog_model.fasta
        │
        ▼
[diamond makedb] ──────────────► card_db.dmnd
                                       │
sample.fasta ──► [diamond blastx] ─────► result.tsv
                                               │
                                     (identifies which ARGs
                                      are in the sample)

card.json
    │
    ▼
[parse_card.py] ──► card_extracted.json
    │
    ▼
[chunk_card.py] ──► card_chunks.json
    │
    ▼
[embed_card_chunks.py] ──► card_embeddings.json  (text → vectors)
    │
    ▼
[build_faiss_index.py] ──► card_faiss.index  (vector search index)
    │
    ▼
[search_card.py] ──► Top-K relevant ARG chunks
    │
    ▼
[llm_reasoning.py] ──► Final AI-generated answer
```

---

##  Generated Files Summary

| File | Generated By | Description |
|------|-------------|-------------|
| `card_db.dmnd` | `diamond makedb` | DIAMOND protein database |
| `result.tsv` | `diamond blastx` | Sequence alignment results |
| `card_extracted.json` | `parse_card.py` | Cleaned ARG entries from CARD |
| `card_chunks.json` | `chunk_card.py` | 150-word text chunks per gene |
| `card_embeddings.json` | `embed_card_chunks.py` | Vectors + metadata for all chunks |
| `card_faiss.index` | `build_faiss_index.py` | Searchable FAISS vector index |

---

##  Technologies Used

| Tool/Library | Purpose |
|---|---|
| **DIAMOND** | Fast protein sequence alignment (like BLAST but faster) |
| **CARD** | Comprehensive Antibiotic Resistance Database — knowledge source |
| **sentence-transformers** | Converts text to semantic vector embeddings |
| **FAISS** | Efficient vector similarity search (AI's memory) |
| **PyTorch / Transformers** | Deep learning backbone for the LLM |
| **NumPy** | Numerical array operations for embedding vectors |

---

##  Key Concepts Summary

| Concept | Simple Explanation |
|---|---|
| **Embedding** | A number array that captures the "meaning" of a text |
| **FAISS** | A search engine for finding similar embeddings instantly |
| **Chunking** | Splitting long text into small pieces so embeddings are focused |
| **RAG** | Give LLM a relevant knowledge snippet before asking it a question |
| **ARO** | Antibiotic Resistance Ontology — standardized ID system for ARGs |
| **DIAMOND blastx** | Translate DNA → protein, then align against a protein database |

---

##  Project Directory Structure

```
arg_llm_project/
├── data/
│   ├── card.json                          # Raw CARD database
│   ├── protein_fasta_protein_homolog_model.fasta
│   ├── nucleotide_fasta_protein_homolog_model.fasta
│   ├── card_db.dmnd                       # DIAMOND database
│   ├── result.tsv                         # Alignment results
│   ├── card_extracted.json                # Parsed gene entries
│   ├── card_chunks.json                   # Text chunks
│   ├── card_embeddings.json               # Embeddings + metadata
│   └── card_faiss.index                   # FAISS vector index
├── parse_card.py                          # Step 4: Parse CARD JSON
├── chunk_card.py                          # Step 5: Chunk descriptions
├── embed_card_chunks.py                   # Step 6: Generate embeddings
├── build_faiss_index.py                   # Step 7: Build FAISS index
├── search_card.py                         # Step 8: Semantic search
└── llm_reasoning.py                       # Step 9: LLM answer generation
```
