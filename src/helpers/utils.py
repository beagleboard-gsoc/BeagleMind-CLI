"""
Utils Module
General utility functions and helpers
"""

import json
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Utils:
    """General utility functions"""

    @staticmethod
    def clean_llm_response_text(response: str) -> str:
        """Remove chain-of-thought style content and leave the final answer.

        Heuristics:
        - Strip <think>/<thinking> blocks if present
        - Drop leading paragraphs that look like internal planning ("I should...", "Let's...", etc.)
        """
        if not response:
            return response
        try:
            # Remove explicit thought tags
            cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)

            # Split into paragraphs and filter obvious meta-thought before first real paragraph
            paras = re.split(r'\n{2,}', cleaned.strip())
            meta_patterns = [
                r"\bI (should|need to|will|am going to|must)\b",
                r"\bLet's\b",
                r"\bPlan:?\b",
                r"\bReasoning:?\b",
                r"\bThinking:?\b",
                r"\bTime to\b",
                r"\bAlright\b",
                r"\bI'll\b",
                r"\bI need to make sure\b",
            ]
            meta_re = re.compile("|".join(meta_patterns), re.IGNORECASE)
            filtered = []
            non_meta_seen = False
            for p in paras:
                if not non_meta_seen and meta_re.search(p):
                    # skip meta planning paragraphs at the start
                    continue
                p2 = re.sub(r'^(?:Note:|Meta:).*$', '', p, flags=re.IGNORECASE | re.MULTILINE).strip()
                if p2:
                    filtered.append(p2)
                    non_meta_seen = True
            cleaned = "\n\n".join(filtered) if filtered else cleaned.strip()

            # Normalize whitespace
            cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
            return cleaned
        except Exception:
            return response

    @staticmethod
    def parse_tool_arguments(args_str: str, function_name: str) -> Dict[str, Any]:
        """Parse tool arguments from malformed JSON string"""
        try:
            # Try to fix JSON by removing problematic characters
            cleaned_args = re.sub(r'[\n\r\t]', ' ', args_str)
            cleaned_args = re.sub(r'\s+', ' ', cleaned_args)
            return json.loads(cleaned_args)
        except:
            # Enhanced argument extraction for different tools
            if function_name == "run_command":
                # Extract command from malformed JSON
                try:
                    command_match = re.search(r'"command":\s*"([^"]*)"', args_str)
                    if command_match:
                        return {"command": command_match.group(1)}
                    # Try multiple patterns
                    patterns = [
                        r'"command":\s*"([^"]*)"',  # Lines 350-351 omitted
                        r'"command":\s*"([^"]*?)(?:"|$)',  # Lines 351-352 omitted
                        r'"command":\s*([^,}]*)',  # Lines 352-353 omitted
                    ]

                    for pattern in patterns:
                        match = re.search(pattern, args_str)
                        if match:
                            return {"command": match.group(1).strip()}

                    return {"command": "echo 'Command parsing failed'"}
                except Exception:
                    return {"command": "echo 'Command parsing failed'"}

            elif function_name == "write_file":
                # Extract file_path and content from malformed JSON
                try:
                    file_path_match = re.search(r'"file_path":\s*"([^"]*)"', args_str)
                    content_match = re.search(r'"content":\s*"([^"]*)"', args_str, re.DOTALL)

                    file_path = file_path_match.group(1) if file_path_match else "recovered_file.txt"
                    content = content_match.group(1) if content_match else "# Content could not be recovered"

                    return {
                        "file_path": file_path,
                        "content": content
                    }
                except Exception:
                    return {
                        "file_path": "error_recovery.txt",
                        "content": "# Failed to parse original content"
                    }
            else:
                # For other functions, try basic recovery
                try:
                    # Attempt to fix JSON by removing problematic characters
                    cleaned_args = re.sub(r'[\n\r\t]', ' ', args_str)
                    cleaned_args = re.sub(r'\s+', ' ', cleaned_args)
                    return json.loads(cleaned_args)
                except:
                    return {}

    @staticmethod
    def format_tool_feedback(function_name: str, function_args: Dict[str, Any], success: bool, error_msg: str = "") -> str:
        """Format tool execution feedback"""
        if success:
            if function_name == "write_file":
                file_path = function_args.get('file_path', 'Unknown')
                content_size = len(function_args.get('content', ''))
                return f"[Success] {function_name}\n   File written: {file_path}\n   Size: {content_size} bytes"

            elif function_name == "edit_file_lines":
                file_path = function_args.get('file_path', 'Unknown')
                edits = function_args.get('edits', {})
                return f"[Success] {function_name}\n   File edited: {file_path}\n   Lines modified: {len(edits)}"

            elif function_name == "read_file":
                file_path = function_args.get('file_path', 'Unknown')
                return f"[Success] {function_name}\n   File read: {file_path}"

            elif function_name == "run_command":
                command = function_args.get('command', 'Unknown')
                return f"[Success] {function_name}\n   Command: {command[:50]}{'...' if len(command) > 50 else ''}"

            elif function_name == "search_in_files":
                pattern = function_args.get('pattern', 'Unknown')
                directory = function_args.get('directory', 'Unknown')
                return f"[Success] {function_name}\n   Searched '{pattern}' in {directory}"

            elif function_name == "show_directory_tree":
                directory = function_args.get('directory', 'Unknown')
                return f"[Success] {function_name}\n   Directory tree: {directory}"

            elif function_name == "analyze_code":
                file_path = function_args.get('file_path', 'Unknown')
                return f"[Success] {function_name}\n   Code analyzed: {file_path}"

            else:
                return f"[Success] {function_name}"

        else:
            return f"[Failed] {function_name}\n   Error: {error_msg}"

    @staticmethod
    def build_context_from_docs(context_docs: List[Dict[str, Any]]) -> str:
        """Build context string from document list"""
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            try:
                # Ensure doc is a dictionary before accessing attributes
                if not isinstance(doc, dict):
                    continue

                file_info = doc.get('file_info', {})
                metadata = doc.get('metadata', {})
                doc_text = doc.get('text', '')

                context_part = f"Document {i}:\n"
                context_part += f"File: {file_info.get('name', 'Unknown')} ({file_info.get('type', 'unknown')})\n"

                if metadata.get('source_link'):
                    context_part += f"Source: {metadata.get('source_link')}\n"

                context_part += f"Content:\n{doc_text}\n"
                context_parts.append(context_part)
            except Exception as e:
                logger.warning(f"Error processing document {i}: {e}")
                continue

        return "\n" + "="*50 + "\n".join(context_parts) if context_parts else ""

    @staticmethod
    def prepare_sources_for_response(context_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare sources list for response formatting"""
        sources = []
        for doc in context_docs:
            try:
                if isinstance(doc, dict):
                    source_info = {
                        "content": doc.get('text', ''),
                        "file_name": doc.get('file_info', {}).get('name', 'Unknown'),
                        "file_type": doc.get('file_info', {}).get('type', 'unknown'),
                        "source_link": doc.get('metadata', {}).get('source_link'),
                        "composite_score": round(doc.get('composite_score', 0.0), 3)
                    }
                else:
                    # Handle case where doc is a string or other type
                    source_info = {
                        "content": str(doc)[:500] + "..." if len(str(doc)) > 500 else str(doc),
                        "file_name": "Unknown",
                        "file_type": "unknown",
                        "source_link": None,
                        "composite_score": 0.0
                    }
                sources.append(source_info)
            except Exception as e:
                logger.warning(f"Error processing source info: {e}")
                # Add a basic fallback source
                sources.append({
                    "content": "Error processing source",
                    "file_name": "Unknown",
                    "file_type": "unknown",
                    "source_link": None,
                    "composite_score": 0.0
                })
                continue

        return sources


# Global instance
utils = Utils()