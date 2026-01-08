import json
docs = [{'id':i,'text':'GSoC '+chr(65+i)+' Project: BeagleMind RAG CLI. Mentors: Fayez. Timeline: Jan-Mar prep','source':'demo'}for i in range(10)]
with open('gsoc_rag_fixed.jsonl','w') as f:
    for d in docs:
        f.write(json.dumps(d)+'\n')
print('✅ 10 fixed docs ready!')
