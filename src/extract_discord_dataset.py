import json
with open('data/BeagleBoard.org - discord gsoc.jsonl','r',encoding='utf-8') as f:data=json.load(f)
docs=[{"id":i+1,"text":msg["author"]["name"]+": "+msg["content"][:500],"source":"gsoc"}for i,msg in enumerate(data["messages"][:500])]
with open('gsoc_rag.jsonl','w',encoding='utf-8') as o:[json.dump(d,o,ensure_ascii=False)for d in docs];o.write('\n'*len(docs))
print('✅',len(docs),'GSoC docs ready!')


 
