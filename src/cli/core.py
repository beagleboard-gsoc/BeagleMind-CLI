"""
Core BeagleMind CLI client functionality.
"""

import logging
import os
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..qa_system import QASystem
from ..config import ConfigManager, COLLECTION_NAME
from .display import DisplayManager
from ..services.doctor_service import DoctorService

# Setup logging
logger = logging.getLogger(__name__)

# CLI Configuration file path
CLI_CONFIG_PATH = os.path.expanduser("~/.beaglemind_cli_config.json")


class BeagleMindCLI:
    """Core BeagleMind CLI client"""

    def __init__(self):
        self.qa_system = None
        self.config_manager = ConfigManager()

    def get_qa_system(self):
        """Get or create QA system instance"""
        if not self.qa_system:
            collection_name = self.config_manager.get("collection_name", COLLECTION_NAME)
            self.qa_system = QASystem(collection_name=collection_name)
            # Initialize a fresh in-RAM conversation for this CLI session
            try:
                self.qa_system.start_conversation()
            except Exception:
                pass
        return self.qa_system

    def list_models(self, backend: str = None):
        """List available models for specified backend or all backends"""
        from .display import DisplayManager
        display = DisplayManager()

        table_data = []
        backends_to_show = [backend] if backend else self.config_manager.get_backends()

        for backend_name in backends_to_show:
            models = self.config_manager.get_models(backend_name)
            model_type = "Local" if backend_name == "ollama" else "Cloud"

            for model in models:
                status = self._check_model_availability(backend_name, model)
                table_data.append({
                    "backend": backend_name.upper(),
                    "model": model,
                    "type": model_type,
                    "status": status
                })

        display.show_models_table(table_data, self._get_current_config_info())

    def _check_model_availability(self, backend: str, model: str) -> str:
        """Check if a model is available"""
        try:
            models = self.config_manager.get_models(backend)
            return "Available" if model in models else "Unknown"
        except Exception:
            return "Check Failed"

    def _get_current_config_info(self) -> Dict[str, Any]:
        """Get current configuration information"""
        backend = self.config_manager.get("default_backend", "groq")
        available_models = self.config_manager.get_models(backend)
        default_model = available_models[0] if available_models else "unknown-model"

        return {
            "backend": backend.upper(),
            "model": self.config_manager.get("default_model", default_model),
            "temperature": self.config_manager.get("default_temperature", 0.3)
        }

    def chat(self, prompt: str, backend: str = None, model: str = None,
             temperature: float = None, search_strategy: str = "adaptive",
             show_sources: bool = False, use_tools: bool = True):
        """Chat with BeagleMind using the specified parameters"""
        from .display import DisplayManager
        display = DisplayManager()

        # Create QA system if not exists
        if not self.qa_system:
            self.qa_system = self.get_qa_system()

        if not prompt.strip():
            display.show_warning("Empty prompt provided.")
            return

        # Get validated parameters
        params = self._get_chat_params(backend, model, temperature)
        if not params:
            return

        try:
            with display.show_spinner("Processing your question..."):
                result = self.qa_system.ask_question(
                    question=prompt,
                    search_strategy=search_strategy,
                    model_name=params["model"],
                    temperature=params["temperature"],
                    llm_backend=params["backend"],
                    use_tools=use_tools
                )

            display.show_chat_response(result, show_sources)

        except Exception as e:
            display.show_error(f"Failed to process question: {e}")
            logger.error(f"Chat error: {e}", exc_info=True)

    def _get_chat_params(self, backend: str = None, model: str = None,
                        temperature: float = None) -> Optional[Dict[str, Any]]:
        """Get and validate chat parameters"""
        from .display import DisplayManager
        display = DisplayManager()

        backend = backend or self.config_manager.get("default_backend", "groq")
        available_backends = self.config_manager.get_backends()

        if backend not in available_backends:
            display.show_warning(f"Backend '{backend}' not recognized. Falling back to default backend.")
            backend = self.config_manager.get("default_backend", "groq")

        available_models = self.config_manager.get_models(backend)
        default_model = available_models[0] if available_models else "unknown-model"
        model = model or self.config_manager.get("default_model", default_model)
        temperature = temperature if temperature is not None else self.config_manager.get("default_temperature", 0.3)
        
        if model not in available_models:
            display.show_warning(f"Model '{model}' not available for backend '{backend}'. Falling back to '{default_model}'.")
            model = self.config_manager.get("default_model", default_model)

        return {
            "backend": backend,
            "model": model,
            "temperature": temperature
        }

    def interactive_chat(self, backend: str = None, model: str = None,
                        temperature: float = None, search_strategy: str = "adaptive",
                        show_sources: bool = False, use_tools: bool = False, collection: str = None):
        """Start an interactive chat session with BeagleMind"""
        from .display import DisplayManager
        from .interactive import InteractiveChat
        display = DisplayManager()

        # Handle collection override
        if collection:
            self.config_manager.set("collection_name", collection)
            self.qa_system = None

        if not self.qa_system:
            self.qa_system = self.get_qa_system()

        # Get validated parameters
        params = self._get_chat_params(backend, model, temperature)
        if not params:
            return

        # Start interactive chat
        chat_session = InteractiveChat(self.qa_system, display, params)
        chat_session.start(
            search_strategy=search_strategy,
            show_sources=show_sources,
            use_tools=use_tools
        )

    def doctor(self):
        """Run system diagnostics and display results"""
        display = DisplayManager()
        doctor = DoctorService()
        
        with display.show_spinner("Running diagnostics..."):
            results = doctor.run_all_checks()
        
        display.show_doctor_results(results)