import json
from pathlib import Path

INPUT_FILE = Path("data/card.json")
OUTPUT_FILE = Path("data/card_extracted.json")


def is_real_gene(obj: dict) -> bool:
    return any(k in obj for k in ["name", "ARO_accession", "accession", "protein_sequence"])


def extract_card_entries(card_data):
    results = []

    for gene_key, gene_info in card_data.items():

        if not isinstance(gene_info, dict):
            continue

        if "ARO_accession" not in gene_info:
            continue

        gene_name = gene_info.get("ARO_name", "").strip()
        aro_id = gene_info.get("ARO_accession", "").strip()
        description = gene_info.get("ARO_description", "").strip()

        mechanism = ""
        aro_category = gene_info.get("ARO_category", {})
        if isinstance(aro_category, dict):
            for cat in aro_category.values():
                if isinstance(cat, dict) and "category_aro_name" in cat:
                    mechanism = cat.get("category_aro_name", "")
                    break

        results.append({
            "gene_name": gene_name,
            "aro_id": aro_id,
            "description": description,
            "mechanism": mechanism
        })

    return results


def main():
    print("[+] Loading CARD JSON...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        card_data = json.load(f)

    print("[+] Extracting gene information...")

    extracted = extract_card_entries(card_data)

    print(f"[+] Extracted {len(extracted)} genes")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)

    print(f"[+] Saved to {OUTPUT_FILE}")

    print("\nSample entries:")
    for i in range(min(3, len(extracted))):
        print(extracted[i])


if __name__ == "__main__":
    main()
