"""
Doctor Service Module
Provides system diagnostics for BeagleMind CLI
"""

import os
import json
import requests
from typing import Dict, Any
from pathlib import Path


class DoctorService:
    """Service for running system diagnostics"""

    def __init__(self):
        self.results = {
            "config": {},
            "api_keys": {},
            "rag_backend": {},
            "ollama": {},
            "overall_status": "unknown"
        }

    def check_config(self) -> Dict[str, Any]:
        """Validate ~/.beaglemind_config.json exists and is valid JSON"""
        config_path = Path.home() / ".beaglemind_config.json"
        
        try:
            if not config_path.exists():
                return {
                    "status": "warning",
                    "message": "Config file not found",
                    "detail": "Run 'beaglemind chat' to create default config",
                    "path": str(config_path)
                }
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ["default_backend", "default_model", "available_backends"]
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                return {
                    "status": "error",
                    "message": "Config missing required fields",
                    "detail": f"Missing: {', '.join(missing_fields)}",
                    "path": str(config_path)
                }
            
            return {
                "status": "success",
                "message": "Config is valid",
                "detail": f"Backend: {config.get('default_backend')}, Model: {config.get('default_model')}",
                "path": str(config_path)
            }
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": "Config has invalid JSON",
                "detail": f"JSON error at line {e.lineno}: {e.msg}",
                "path": str(config_path)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to read config",
                "detail": str(e),
                "path": str(config_path)
            }

    def check_api_keys(self) -> Dict[str, Any]:
        """Verify API keys are set in environment"""
        keys_to_check = {
            "GROQ_API_KEY": "Groq (cloud)",
            "OPENAI_API_KEY": "OpenAI (cloud)",
            "OPENROUTER_API_KEY": "OpenRouter (optional)"
        }
        
        results = {}
        any_set = False
        
        for key, description in keys_to_check.items():
            value = os.getenv(key)
            is_set = bool(value and len(value) > 0)
            
            if is_set and key != "OPENROUTER_API_KEY":
                any_set = True
            
            results[key] = {
                "set": is_set,
                "description": description,
                "optional": key == "OPENROUTER_API_KEY"
            }
        
        if not any_set:
            status = "error"
            message = "No API keys configured"
            detail = "Set at least GROQ_API_KEY or OPENAI_API_KEY"
        else:
            status = "success"
            message = "API keys configured"
            detail = None
        
        return {
            "status": status,
            "message": message,
            "detail": detail,
            "keys": results
        }

    def check_rag_backend(self) -> Dict[str, Any]:
        """Check RAG backend connectivity and latency"""
        backend_url = os.getenv("RAG_BACKEND_URL", "https://mind-api.beagleboard.org/api")
        
        try:
            import time
            start = time.time()
            response = requests.get(f"{backend_url}/health", timeout=5)
            latency = int((time.time() - start) * 1000)  # ms
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "RAG backend online",
                    "detail": f"Latency: {latency}ms",
                    "url": backend_url,
                    "latency_ms": latency
                }
            else:
                return {
                    "status": "warning",
                    "message": f"RAG backend returned {response.status_code}",
                    "detail": "Backend may be experiencing issues",
                    "url": backend_url
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "RAG backend timeout",
                "detail": "Backend not responding (>5s)",
                "url": backend_url
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "RAG backend offline",
                "detail": "Cannot connect to backend",
                "url": backend_url
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "RAG backend check failed",
                "detail": str(e),
                "url": backend_url
            }

    def check_ollama(self) -> Dict[str, Any]:
        """Check if Ollama server is running and list models"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name") for m in models]
                
                if not models:
                    return {
                        "status": "warning",
                        "message": "Ollama running but no models",
                        "detail": "Run 'ollama pull <model>' to download a model",
                        "url": "http://localhost:11434"
                    }
                
                return {
                    "status": "success",
                    "message": "Ollama running",
                    "detail": f"{len(models)} model(s) available",
                    "url": "http://localhost:11434",
                    "models": model_names
                }
            else:
                return {
                    "status": "error",
                    "message": f"Ollama returned {response.status_code}",
                    "detail": "Ollama may be misconfigured",
                    "url": "http://localhost:11434"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "status": "info",
                "message": "Ollama not running",
                "detail": "Optional - only needed for local models",
                "url": "http://localhost:11434"
            }
        except Exception as e:
            return {
                "status": "warning",
                "message": "Could not check Ollama",
                "detail": str(e),
                "url": "http://localhost:11434"
            }

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all diagnostic checks and return results"""
        self.results["config"] = self.check_config()
        self.results["api_keys"] = self.check_api_keys()
        self.results["rag_backend"] = self.check_rag_backend()
        self.results["ollama"] = self.check_ollama()
        
        # Determine overall status
        statuses = [
            self.results["config"]["status"],
            self.results["api_keys"]["status"],
            self.results["rag_backend"]["status"],
        ]
        
        if "error" in statuses:
            self.results["overall_status"] = "error"
        elif "warning" in statuses:
            self.results["overall_status"] = "warning"
        else:
            self.results["overall_status"] = "success"
        
        return self.results
