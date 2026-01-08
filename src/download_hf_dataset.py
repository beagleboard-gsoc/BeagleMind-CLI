from datasets import load_dataset

ds = load_dataset("fayezzouari/beagleboard-docs", split="train")  # [web:73][web:83]

print(ds)
print(ds.column_names)

# Example: save to JSONL for your RAG
output_path = "data/beagleboard_docs.jsonl"
ds.to_json(output_path, lines=True, force_ascii=False)
print("Saved to", output_path)
