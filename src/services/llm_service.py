"""
LLM Service Module
Handles interactions with different LLM backends (Groq, OpenAI, Ollama)
"""

import os
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class LLMService:
    """Service for handling LLM backend interactions"""

    def __init__(self):
        pass

    def chat_with_openai(self, messages: List[Dict], model_name: str, temperature: float, tools: Optional[List[Dict]] = None) -> Tuple[str, List[Dict]]:
        """Handle chat with OpenAI backend"""
        from openai import OpenAI

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file or environment variables.")

        client = OpenAI(
            api_key=api_key,
            timeout=30.0
        )

        tools = tools or []

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature,
                timeout=25.0
            )

            message = completion.choices[0].message
            content = message.content or ""
            tool_calls = []

            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })

            return content, tool_calls

        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return f"Error communicating with OpenAI: {str(e)}", []

    def chat_with_groq(self, messages: List[Dict], model_name: str, temperature: float, tools: Optional[List[Dict]] = None) -> Tuple[str, List[Dict]]:
        """Handle chat with Groq backend"""
        from openai import OpenAI
        from ..config import GROQ_API_KEY

        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set. Please set it in your .env file or environment variables.")

        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            timeout=30.0
        )

        tools = tools or []
        
       

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature,
                timeout=25.0
            )

            message = completion.choices[0].message
            content = message.content or ""
            tool_calls = []

            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })

            return content, tool_calls

        except Exception as e:
            logger.error(f"Groq chat error: {e}")
            return f"Error communicating with Groq: {str(e)}", []

    def chat_with_ollama(self, messages: List[Dict], model_name: str, temperature: float, tools: Optional[List[Dict]] = None) -> Tuple[str, List[Dict]]:
        """Handle chat with Ollama backend"""
        from openai import OpenAI

        client = OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1",
            timeout=360.0
        )
        # Per policy, Ollama MUST NOT have access to tool calling. Do not pass tools.
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                timeout=360.0
            )

            message = completion.choices[0].message
            content = message.content or ""
            tool_calls = []

            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": getattr(tc, 'id', f"call_{len(tool_calls)}"),
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })

            return content, tool_calls

        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return f"Error communicating with Ollama: {str(e)}", []

    def get_response_openai(self, prompt: str, model_name: str, temperature: float) -> str:
        """Get response from OpenAI LLM"""
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=30.0
        )

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                timeout=25.0
            )

            return completion.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI response error: {e}")
            return f"Error getting response from OpenAI: {str(e)}"

    def get_response_groq(self, prompt: str, model_name: str, temperature: float) -> str:
        """Get response from Groq LLM"""
        from openai import OpenAI
        from ..config import GROQ_API_KEY

        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            timeout=30.0
        )

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                timeout=25.0
            )

            return completion.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"Groq response error: {e}")
            return f"Error getting response from Groq: {str(e)}"

    def get_response_ollama(self, prompt: str, model_name: str, temperature: float) -> str:
        """Get response from Ollama LLM"""
        from openai import OpenAI

        client = OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1",
            timeout=360.0
        )

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                timeout=360.0
            )

            return completion.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"Ollama response error: {e}")
            return f"Error getting response from Ollama: {str(e)}"

    def call_llm_with_fallback(self, prompt: str, preferred_backend: str, model_name: str, temperature: float) -> Tuple[str, Optional[str]]:
        """Attempt preferred backend, then fall back to other backends if errors occur.

        Returns (answer_str, used_backend)
        """
        backends_try = [preferred_backend.lower()]
        for b in ['ollama', 'openai', 'groq']:
            if b not in backends_try:
                backends_try.append(b)

        last_err = None
        for backend in backends_try:
            try:
                if backend == 'groq':
                    ans = self.get_response_groq(prompt, model_name, temperature)
                elif backend == 'openai':
                    ans = self.get_response_openai(prompt, model_name, temperature)
                elif backend == 'ollama':
                    ans = self.get_response_ollama(prompt, model_name, temperature)
                else:
                    continue

                # Treat explicit error-prefixed responses as failure to try next
                if isinstance(ans, str) and ans.startswith('Error getting response from'):
                    last_err = ans
                    continue

                return ans, backend
            except Exception as e:
                last_err = str(e)
                logger.warning(f"Backend {backend} failed, trying next: {e}")
                continue

        # All backends failed
        return (last_err or "No LLM backend available"), None


# Global instance
llm_service = LLMService()