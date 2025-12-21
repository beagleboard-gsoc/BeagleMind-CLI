import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

OUTPUT_PATH = DATA_DIR / "qa_dataset_docs.jsonl"

def build_docs_qa():
    """Build a tiny QA dataset from hardcoded examples for now."""
    qa_examples = [
        {
            "question": "What is BeagleMind?",
            "answer": "BeagleMind is an intelligent documentation assistant for Beagleboard projects that uses RAG and multiple LLM providers.",
            "source_type": "docs",
            "source_id": "internal:overview",
            "tags": ["beaglemind", "overview"],
        },
        {
            "question": "Which LLM providers does BeagleMind support?",
            "answer": "BeagleMind currently supports OpenAI, OpenRouter, Groq, and Ollama via an extensible provider abstraction.",
            "source_type": "docs",
            "source_id": "internal:providers",
            "tags": ["providers", "llm"],
        },
    ]

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for row in qa_examples:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(qa_examples)} QA examples to {OUTPUT_PATH}")

if __name__ == "__main__":
    build_docs_qa()
