import os
import json
from dotenv import load_dotenv

load_dotenv()

MILVUS_URI = os.getenv("MILVUS_URI")

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = "mixtral-8x7b-32768"  # or "llama2-70b-4096"

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Vector Store Configuration
VECTOR_STORE_PATH = "repository_content"
EMBEDDINGS_MODEL = "BAAI/bge-m3"

# Reranking Configuration
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RERANK_TOP_K = 5

# Collection Configuration (env override supported)
COLLECTION_NAME = 'beagleboard'

RAG_BACKEND_URL = 'https://mind-api.beagleboard.org/api'

import os
import json

class ConfigManager:
    def __init__(self, path="~/.beaglemind_config.json"):
        self.path = os.path.expanduser(path)
        self.default_config = {
            "collection_name": "default_collection",
            "default_backend": "groq",
            "default_model": "llama-3.3-70b-versatile",
            "default_temperature": 0.3,
            "default_use_tools": False,
            # Configuration metadata
            "available_backends": ["groq", "openai", "ollama"],
            "available_models": {
                "groq": [
                    "llama-3.3-70b-versatile",
                    "llama-3.1-8b-instant",
                    "gemma2-9b-it",
                    "meta-llama/llama-4-scout-17b-16e-instruct",
                    "meta-llama/llama-4-maverick-17b-128e-instruct",
                    "deepseek-r1-distill-llama-70b"
                ],
                "openai": [
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo",
                    "o1-preview",
                    "o1-mini"
                ],
                "ollama": [
                    "huihui_ai/qwen2.5-coder-abliterate:0.5b",
                    "deepseek-r1:1.5b",
                    "smollm2:135m",
                    "smollm2:360m",
                    "qwen3:1.7b",
                    "qwen2.5-coder:0.5b",
                    "gemma3:270m"
                ]
            }
        }

        self.config = self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Config file corrupted. Loading defaults.")
        else:
            self.save(self.default_config)
        return self.default_config.copy()

    def save(self, data=None):
        if data is None:
            data = self.config
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, self.default_config.get(key, default))

    def set(self, key, value):
        self.config[key] = value
        self.save()

    #Backend management
    def get_backends(self):
        return self.config.get("available_backends", self.default_config["available_backends"])

    def get_models(self, backend):
        models = self.config.get("available_models", {}).get(backend)
        if not models:
            # fallback to defaults if missing
            models = self.default_config["available_models"].get(backend, [])
        return models

    def add_model(self, backend, model_name):
        models = self.config.setdefault("available_models", {}).setdefault(backend, [])
        if model_name not in models:
            models.append(model_name)
            self.save()

    def remove_model(self, backend, model_name):
        models = self.config.get("available_models", {}).get(backend, [])
        if model_name in models:
            models.remove(model_name)
            self.save()
