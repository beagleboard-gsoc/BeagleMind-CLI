import gradio as gr
import json
import os

# Safe dataset load - YOUR discord_gsoc_docs.jsonl (184 docs!)
filename = 'discord_gsoc_docs.jsonl'
docs = []
if os.path.exists(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        doc = json.loads(line)
                        if 'text' in doc:  # Ensure has text
                            docs.append(doc)
                    except json.JSONDecodeError as e:
                        print(f"Skip line {line_num}: {e}")
                        continue
        print(f"✅ Loaded {len(docs)} valid GSoC Discord docs from {filename}!")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"❌ {filename} not found!")
    docs = [{"id":1, "text":"Demo GSoC conversation ready! Put discord_gsoc_docs.jsonl here.", "source":"gsoc"}]

def gsoc_rag(query):
    print(f"🔍 '{query}' | Docs: {len(docs)}")
    if not docs:
        return "No docs"
    
    query_lower = query.lower()
    best_docs = []  # Top 3 docs
    
    for doc in docs:
        score = 0
        doc_text = doc['text'].lower()
        
        # PRIORITY 1: Exact phrase match (HIGHEST weight)
        if query_lower in doc_text:
            score += 100
        
        # PRIORITY 2: Key BeagleMind words (specific to your dataset)
        beagle_words = ['beagle', 'beaglemind', 'beagleboard', 'beagle ai', 'rag', 'gsoc']
        query_beagle = sum(1 for w in beagle_words if w in query_lower and w in doc_text)
        score += query_beagle * 25
        
        # PRIORITY 3: Query words anywhere
        words = query_lower.split()
        exact_matches = sum(1 for w in words if w in doc_text)
        score += exact_matches * 10
        
        # PRIORITY 4: Doc length (long convos better)
        score += min(20, len(doc['text']) / 100)
        
        best_docs.append((score, doc))
    
    # Sort by score DESC
    best_docs.sort(key=lambda x: x[0], reverse=True)
    best = best_docs[0][1]  # Highest scoring doc
    
    # FULL TEXT!
    text = best['text']
    preview = text[:2800] + "..." if len(text) > 2800 else text
    
    return f"""🎯 **BEST MATCH: {best_docs[0][0]:.0f}pts** (184 docs → Top 1)

{preview}

🏆 **Doc #{best.get('id', '?')}** | {best.get('source', 'discord')}
⭐ **2nd**: {best_docs[1][0]:.0f}pts | **3rd**: {best_docs[2][0]:.0f}pts"""

# ✅ COMPLETE Interface + Launch
demo = gr.Interface(
    fn=gsoc_rag,
    inputs=gr.Textbox(placeholder="GSoC? BeagleMind? timeline? RAG?", label="🔍 Query"),
    outputs=gr.Textbox(label="💬 Full Discord Answer", lines=25),
    title="🦜 BeagleMind GSoC RAG (184 Docs)",
    examples=[["GSoC"], ["BeagleMind"], ["timeline"], ["RAG PoC"], ["mentor"]]
)

if __name__ == "__main__":
    demo.queue().launch(share=True, server_name="0.0.0.0", server_port=7860)


