import json

print("🔄 Converting Fayez dataset format for RAG...")

with open("data/qa_dataset_docs.jsonl", "r", encoding="utf-8") as f:
    raw_data = [json.loads(line) for line in f]

print(f"Raw: {len(raw_data)} conversations")

# Convert messages → flat text for RAG
rag_data = []
for i, convo in enumerate(raw_data):
    messages = convo["messages"]
    
    # Extract user questions + assistant answers
    for j in range(1, len(messages)-1, 2):  # user-assistant pairs
        if messages[j]["role"] == "user" and messages[j+1]["role"] == "assistant":
            rag_data.append({
                "text": f"Q: {messages[j]['content']}\nA: {messages[j+1]['content']}",
                "source": "fayezzouari/beagleboard-docs",
                "conversation_id": i
            })

print(f"RAG format: {len(rag_data)} Q&A pairs")

# Save RAG-ready format
with open("data/qa_dataset_rag.jsonl", "w", encoding="utf-8") as f:
    for item in rag_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("✅ Saved: data/qa_dataset_rag.jsonl")
print("Use this for RAG indexing!")
