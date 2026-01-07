import json

# Load Discord GSoC data
print("📥 Loading BeagleBoard GSoC Discord...")
with open('data/BeagleBoard.org - discord gsoc.jsonl', 'r', encoding='utf-8') as f:
    data = json.load(f)

messages = data['messages']
print(f"🚀 Total GSoC messages: {len(messages)}")
print(f"⏰ Date range: {messages[0]['timestamp'][:10]} → {messages[-1]['timestamp'][:10]}")
print(f"📢 Channel: {data['channel']['name']}")

# Extract RAG documents (multi-turn conversations)
print("\n🔄 Creating RAG dataset...")
docs = []
current_conv = []
for i, msg in enumerate(messages):
    content = msg['content'].strip()
    if content and len(current_conv) < 8:  # Max 8 turns per doc
        current_conv.append(f"{msg['author']['name']}: {content}")
    elif len(current_conv) >= 3:  # Min 3 turns = valid convo
        docs.append({
            'id': len(docs) + 1,
            'text': '\n'.join(current_conv),
            'source': 'discord-gsoc',
            'channel': data['channel']['name'],
            'turns': len(current_conv)
        })
        current_conv = []
    if len(docs) >= 500:  # Scope target
        break

# Save RAG dataset
with open('../gsoc_rag_dataset.jsonl', 'w', encoding='utf-8') as f:
    for doc in docs:
        f.write(json.dumps(doc, ensure_ascii=False) + '\n')

print(f"✅ {len(docs)} RAG conversations saved!")
print(f"📁 File: gsoc_rag_dataset.jsonl")
print("\n🎉 BeagleMind GSoC RAG DATASET v1 COMPLETE!")
print("Next: Gradio integration + test queries")
