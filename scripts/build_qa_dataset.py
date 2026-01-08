import json
from pathlib import Path
from datetime import datetime, timedelta
import os
import re

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

UNIFIED_OUTPUT = DATA_DIR / "qa_dataset_unified.jsonl"
SAMPLE_OUTPUT = DATA_DIR / "qa_dataset_unified_sample.jsonl"

def _parse_date(dt_str):
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None

def _clean(s):
    if not isinstance(s, str):
        return ""
    return s.replace("\u2019", "'").replace("\u2014", "-").replace("\u2013", "-")

def _pairwise_qa(messages):
    items = []
    for j in range(0, len(messages) - 1):
        a = messages[j]
        b = messages[j + 1]
        if a.get("role") == "user" and b.get("role") in ("assistant", "bot"):
            q = _clean(a.get("content", ""))
            ans = _clean(b.get("content", ""))
            if len(q.strip()) >= 8 and len(ans.strip()) >= 8:
                items.append((q, ans, a, b))
    return items

def _extract_username(msg, fallback_text=""):
    name = msg.get("username") or msg.get("author") or msg.get("name")
    if name:
        return str(name)
    m = re.search(r"user\s+([A-Za-z0-9_]+)", fallback_text)
    return m.group(1) if m else None

def load_jsonl(path):
    rows = []
    if not Path(path).exists():
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows

def convert_conversations_to_qa(rows, source_type, start_dt=None, end_dt=None):
    qa_rows = []
    for i, row in enumerate(rows):
        msgs = row.get("messages") or []
        if len(msgs) < 2:
            continue
        if start_dt or end_dt:
            msg_dates = []
            for m in msgs:
                d = _parse_date(m.get("timestamp") or m.get("created_at") or "")
                if d:
                    msg_dates.append(d)
            if msg_dates:
                newest = max(msg_dates)
                oldest = min(msg_dates)
                if start_dt and newest < start_dt:
                    continue
                if end_dt and oldest > end_dt:
                    continue
        pairs = _pairwise_qa(msgs)
        if not pairs:
            continue
        for (q, ans, qa_msg, ans_msg) in pairs:
            username = _extract_username(ans_msg, ans) or _extract_username(qa_msg, q)
            qa_rows.append({
                "question": q,
                "answer": ans,
                "source_type": source_type,
                "source_id": row.get("source_id") or row.get("thread_url") or row.get("conversation_id") or f"{source_type}:{i}",
                "tags": [t for t in row.get("tags", [])] + ([f"user:{username}"] if username else [])
            })
    return qa_rows

def build_unified_qa():
    now = datetime.utcnow()
    default_start = now - timedelta(days=365)
    start_env = os.getenv("DISCORD_START_DATE")
    end_env = os.getenv("DISCORD_END_DATE")
    start_dt = _parse_date(start_env) if start_env else default_start
    end_dt = _parse_date(end_env) if end_env else now

    forum_rows = load_jsonl(DATA_DIR / "forum_conversations.jsonl")
    discord_rows = load_jsonl(DATA_DIR / "discord_conversations.jsonl")

    forum_qa = convert_conversations_to_qa(forum_rows, "forum", start_dt, end_dt)
    discord_qa = convert_conversations_to_qa(discord_rows, "discord", start_dt, end_dt)

    docs_seed = [
        {
            "question": "What is BeagleMind?",
            "answer": "BeagleMind is an intelligent documentation assistant for BeagleBoard projects using RAG.",
            "source_type": "docs",
            "source_id": "internal:overview",
            "tags": ["beaglemind", "overview"]
        },
        {
            "question": "Which providers are supported?",
            "answer": "OpenAI, OpenRouter, Groq, and Ollama are supported via an extensible abstraction.",
            "source_type": "docs",
            "source_id": "internal:providers",
            "tags": ["providers", "llm"]
        }
    ]

    all_qa = docs_seed + forum_qa + discord_qa

    seen = set()
    deduped = []
    for r in all_qa:
        k = (r["question"].strip()[:256], r["answer"].strip()[:256], r["source_type"])
        if k in seen:
            continue
        seen.add(k)
        deduped.append(r)

    with open(UNIFIED_OUTPUT, "w", encoding="utf-8") as f:
        for r in deduped:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    sample = deduped[:20]
    with open(SAMPLE_OUTPUT, "w", encoding="utf-8") as f:
        for r in sample:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(deduped)} rows to {UNIFIED_OUTPUT}")
    print(f"Wrote {len(sample)} rows to {SAMPLE_OUTPUT}")

if __name__ == "__main__":
    build_unified_qa()
