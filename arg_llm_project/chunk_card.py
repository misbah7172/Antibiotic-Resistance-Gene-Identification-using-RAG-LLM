import json
import os

INPUT_FILE = "data/card_extracted.json"
OUTPUT_FILE = "data/card_chunks.json"
CHUNK_SIZE = 150   # words per chunk


def chunk_text(text, chunk_size):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)

    return chunks


def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_chunks = []
    chunk_counter = 0

    for entry in data:
        gene_name = entry.get("gene_name", "")
        aro_id = entry.get("aro_id", "")
        description = entry.get("description", "")
        mechanism = entry.get("mechanism", "")

        combined_text = f"{description}. Mechanism: {mechanism}".strip()

        if not combined_text:
            continue

        chunks = chunk_text(combined_text, CHUNK_SIZE)

        for idx, chunk in enumerate(chunks):
            record = {
                "chunk_id": f"{aro_id}_{idx}",
                "gene_name": gene_name,
                "aro_id": aro_id,
                "text": chunk
            }
            all_chunks.append(record)
            chunk_counter += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print("Done.")
    print(f"Original records: {len(data)}")
    print(f"Total chunks created: {chunk_counter}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
