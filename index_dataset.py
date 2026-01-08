import json
import os
from chromadb import Client
import chromadb.utils.embedding_functions as embedding_functions

# Check repo structure first
print("📁 Current files:")
os.system("dir *.py data\\*.jsonl")

print("\n🔍 Checking qa_system.py...")
try:
    import qa_system
    print("✅ qa_system.py found!")
    print("Available classes:", [name for name in dir(qa_system) if 'QA' in name or 'System' in name])
except:
    print("❌ qa_system.py import failed")

# Manual indexing
print("\n📊 Dataset stats:")
with open("data/qa_dataset_docs.jsonl", "r", encoding="utf-8") as f:
    lines = sum(1 for _ in f)
    print(f"Total conversations: {lines}")

print("\n✅ Dataset ready! CLI auto-loads on startup.")
print("Test with: beaglemind chat --no-tools")
