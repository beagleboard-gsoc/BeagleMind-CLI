from datasets import load_dataset
import json

print("Downloading fayezzouari/beagleboard-docs dataset...")

# Load dataset from Hugging Face
ds = load_dataset("fayezzouari/beagleboard-docs", split="train")

print("Dataset info:")
print(f"Total rows: {len(ds)}")
print(f"Columns: {ds.column_names}")
print("\nFirst row sample:")
print(ds[0])

# Save as JSONL for RAG system
output_path = "data/beagleboard_docs.jsonl"

with open(output_path, "w", encoding="utf-8") as f:
    for row in ds:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"\n✅ Dataset saved to: {output_path}")
print("Ready for RAG indexing!")
