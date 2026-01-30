"""
Prompt Generator Module
Handles generation of context-aware prompts
"""

import re
from typing import List, Dict, Any

from .prompt_templates import PromptTemplates

class PromptGenerator:
    """Service for generating context-aware prompts"""

    def __init__(self):
        # Question type detection patterns
        self.question_patterns = {
            'code': [r'\bcode\b', r'\bfunction\b', r'\bclass\b', r'\bmethod\b', r'\bapi\b', r'\bimplement\b'],
            'documentation': [r'\bdocument\b', r'\bguide\b', r'\btutorial\b', r'\bhow to\b', r'\bexample\b'],
            'concept': [r'\bwhat is\b', r'\bdefine\b', r'\bexplain\b', r'\bconcept\b', r'\bunderstand\b'],
            'troubleshooting': [r'\berror\b', r'\bissue\b', r'\bproblem\b', r'\bfix\b', r'\btroubleshoot\b', r'\bbug\b'],
            'comparison': [r'\bcompare\b', r'\bdifference\b', r'\bversus\b', r'\bvs\b', r'\bbetter\b'],
            'recent': [r'\blatest\b', r'\brecent\b', r'\bnew\b', r'\bupdated\b', r'\bcurrent\b']
        }

    def should_retrieve(self, question: str, backend: str, use_tools: bool) -> bool:
        """Heuristic for deciding retrieval when not using tool-driven chat.

        - Ollama: always True
        - Others: True if question references BeagleBoard/docs or matches technical patterns; False for greetings/irrelevant.
        """
        if (backend or '').lower() == 'ollama':
            return True
        if not question:
            return False
        q = question.lower()
        # Beagleboard hints
        if any(tok in q for tok in ["beagle", "beaglebone", "beagleboard", "beagley-ai", "beagley ai", "bbb"]):
            return True
        # Technical patterns
        for pats in self.question_patterns.values():
            for p in pats:
                try:
                    if re.search(p, q):
                        return True
                except Exception:
                    continue
        # Greetings/irrelevant
        if any(g in q for g in ["hello", "hi", "hey", "what's up", "how are you", "good morning", "good evening"]):
            return False
        return False

    def generate_context_aware_prompt(self, question: str, context_docs: List[Dict[str, Any]],
                                    question_types: List[str]) -> str:
        """Generate a context-aware prompt based on question type"""

        # Build context with metadata
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            file_info = doc.get('file_info', {})
            metadata = doc.get('metadata', {})

            context_part = f"Document {i}:\n"
            context_part += f"File: {file_info.get('name', 'Unknown')} ({file_info.get('type', 'unknown')})\n"

            if file_info.get('language') != 'unknown':
                context_part += f"Language: {file_info.get('language')}\n"

            if metadata.get('source_link'):
                context_part += f"Source Link: {metadata.get('source_link')}\n"

            if metadata.get('raw_url'):
                context_part += f"Raw URL: {metadata.get('raw_url')}\n"

            if metadata.get('has_code'):
                context_part += "Contains: Code\n"
            elif metadata.get('has_documentation'):
                context_part += "Contains: Documentation\n"

            context_part += f"Content:\n{doc['text']}\n"
            context_parts.append(context_part)

        context = "\n" + "="*50 + "\n".join(context_parts)

        # Check if this is a file creation request
        file_creation_keywords = ["create", "make", "generate", "write", "save", "file"]
        is_file_request = any(keyword in question.lower() for keyword in file_creation_keywords)

        if is_file_request:
            # Use a more direct prompt for file operations
            system_prompt = PromptTemplates.get_file_creation_prompt()
        else:
            # Use the full system prompt for other requests
            system_prompt = PromptTemplates.get_general_assistant_prompt()

        prompt = f"""
{system_prompt}

Answer the user's question using only the provided context documents.

---

{context}

Question: {question}

Answer:
"""

        return prompt

    def build_system_prompt_with_context(self, question: str, context: str, backend: str,
                                       machine_info: Dict[str, Any], use_tools: bool = True) -> str:
        """Build system prompt with context for tool-enabled chat"""
        retrieval_guidance = PromptTemplates.get_retrieval_guidance(backend)

        extra_tool_note = ""
        if backend.lower() not in ("ollama",):
            extra_tool_note = "\nAvailable extra tool: retrieve_context(query, n_results=5, rerank=true, collection_name='beagleboard')."

        system_prompt = f"""You are BeagleMind, a concise, reliable assistant for Beagleboard docs and code.

Tools (call when needed): read_file, write_file, edit_file_lines, search_in_files, run_command, analyze_code, show_directory_tree.{extra_tool_note}

Rules:
- {retrieval_guidance}
- Use tools to read/write/modify files or run commands; don't just describe.
- Working dir: {machine_info['current_working_directory']} (base: {machine_info['base_directory']}). Prefer relative paths and confirm created paths.
- Keep answers brief, actionable, and grounded in context.

Context:
{context}
"""

        return system_prompt


# Global instance
prompt_generator = PromptGenerator()