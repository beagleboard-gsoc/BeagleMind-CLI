"""
Conversation Manager Module
Handles conversation history and memory management
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation history and memory"""

    def __init__(self, max_messages: int = 20):
        # In-memory conversation history (RAM-only)
        self.conversation_history: List[Dict[str, str]] = []  # [{role: 'user'|'assistant', content: str}]
        self.max_messages = max_messages

    def start_conversation(self):
        """Begin a new chat session (clears in-RAM history)."""
        self.conversation_history = []

    def reset_conversation(self):
        """Alias to start a new session by clearing history."""
        self.start_conversation()

    def get_history_messages(self) -> List[Dict[str, str]]:
        """Return prior conversation turns as chat messages (capped)."""
        if not self.conversation_history:
            return []
        # Only keep the last N messages
        hist = self.conversation_history[-self.max_messages:]
        # Ensure structure matches OpenAI chat format
        return [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in hist if m.get("content")]

    def record_user(self, content: str):
        if content:
            self.conversation_history.append({"role": "user", "content": str(content)})

    def record_assistant(self, content: str):
        if content is None:
            content = ""
        self.conversation_history.append({"role": "assistant", "content": str(content)})

    def build_messages_for_llm(self, system_prompt: str, user_question: str) -> List[Dict[str, str]]:
        """Build the messages array for LLM API calls"""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.get_history_messages())
        messages.append({
            "role": "user", 
            "content": str(user_question) if user_question else "Hello, I need help with BeagleBoard development."
        })
        return messages

    def add_assistant_message(self, content: str, tool_calls: List[Dict] = None) -> Dict[str, Any]:
        """Add an assistant message to the conversation"""
        message = {
            "role": "assistant",
            "content": content or ""
        }
        
        if tool_calls:
            message["tool_calls"] = tool_calls
            
        self.conversation_history.append(message)
        return message

    def add_tool_message(self, tool_call_id: str, content: str):
        """Add a tool response message to the conversation"""
        self.conversation_history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })

    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        if not self.conversation_history:
            return "No conversation history"

        user_messages = [msg for msg in self.conversation_history if msg.get("role") == "user"]
        assistant_messages = [msg for msg in self.conversation_history if msg.get("role") == "assistant"]

        return f"Conversation with {len(user_messages)} user messages and {len(assistant_messages)} assistant responses"


# Global instance
conversation_manager = ConversationManager()