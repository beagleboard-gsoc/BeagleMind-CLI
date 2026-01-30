"""
Prompt Templates Module
Contains system prompts and prompt templates
"""

from typing import List, Dict, Any

class PromptTemplates:
    """Container for various prompt templates"""

    @staticmethod
    def get_system_prompt_for_tools(context: str, machine_info: Dict[str, Any]) -> str:
        """Get system prompt for tool-enabled chat"""
        return f"""You are BeagleMind, a concise, reliable assistant for Beagleboard docs and code.

Tools (call when needed): read_file, write_file, edit_file_lines, search_in_files, run_command, analyze_code, show_directory_tree.

Rules:
- Use tools to read/write/modify files or run commands; don't just describe.
- Working dir: {machine_info['current_working_directory']} (base: {machine_info['base_directory']}). Prefer relative paths and confirm created paths.
- Keep answers brief, actionable, and grounded in context.

Context:
{context}
"""

    @staticmethod
    def get_fallback_prompt(question: str, history_block: str = "") -> str:
        """Get fallback prompt when no context is available"""
        return (
            "You are BeagleMind, a concise, reliable assistant for Beagleboard tasks.\n\n"
            "No repository context is available for this question. Provide a practical, step-by-step answer "
            "with a small code example when helpful. Keep it accurate and concise.\n\n"
            f"{history_block}Question: {question}\n\nAnswer:"
        )

    @staticmethod
    def get_file_creation_prompt() -> str:
        """Get prompt for file creation operations"""
        return '''You are BeagleMind focused on file operations.

Rule: When asked to create/make/generate/write a file, CALL write_file(file_path, content). Do not only describe.

Tool:
- write_file(file_path, content)
'''

    @staticmethod
    def get_general_assistant_prompt() -> str:
        """Get general assistant prompt for BeagleBoard tasks"""
        return '''You are BeagleMind for Beagleboard docs/code.

Use only the provided context. Keep answers concise and actionable.

Tools (use when appropriate): read_file, write_file, edit_file_lines, search_in_files, run_command, analyze_code, list_directory.

When to call tools:
- create/make/generate/save → write_file
- read/show/display → read_file
- modify/edit/change → edit_file_lines or write_file

Rules:
1) Call tools for file ops, don't just describe.
2) Prefer complete content in write_file.
3) Validate paths and avoid destructive changes without consent.'''

    @staticmethod
    def get_retrieval_guidance(backend: str) -> str:
        """Get retrieval guidance based on backend"""
        if backend.lower() == "ollama":
            return "Context is pre-retrieved and appended below. Use it to answer."
        else:
            return (
                "If the user's question is about BeagleBoard docs or has a technical aspect, call the tool 'retrieve_context' with the query to fetch references; "
                "otherwise, answer directly without retrieval."
            )

    @staticmethod
    def get_retrieve_context_tool() -> Dict[str, Any]:
        """Get the virtual retrieval tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "retrieve_context",
                "description": "Retrieve relevant BeagleBoard documents for a user query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The user question to search for."},
                        "n_results": {"type": "integer", "description": "How many results to return", "default": 5},
                        "rerank": {"type": "boolean", "description": "Whether to rerank results", "default": True},
                        "collection_name": {"type": "string", "description": "Collection name to search (defaults to config)"}
                    },
                    "required": ["query"]
                }
            }
        }