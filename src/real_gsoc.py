import json
data = json.load(open('../data/BeagleBoard.org - discord gsoc.jsonl', 'r', encoding='utf-8'))
docs = []
for msg in data['messages'][:200]:
    if msg['content'].strip():
        docs.append({
            'id':len(docs)+1,
            'text':msg['author']['name'] + ': ' + msg['content'][:800],
            'source':'BeagleBoard #gsoc'
        })
with open('real_gsoc_rag.jsonl','w', encoding='utf-8') as f:
    for d in docs:
        f.write(json.dumps(d, ensure_ascii=False) + '\n')
print(f'✅ {len(docs)} REAL Discord docs!')
