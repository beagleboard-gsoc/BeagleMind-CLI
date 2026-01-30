"""
File operation tools: read, write, edit files.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import get_path_resolver

logger = logging.getLogger(__name__)


def read_file(file_path: str) -> Dict[str, Any]:
    """Read contents of a file"""
    try:
        resolver = get_path_resolver()
        safe_path = resolver.safe_path(file_path)
        
        if not safe_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        if not safe_path.is_file():
            return {"success": False, "error": f"Path is not a file: {file_path}"}
        
        with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Get file info
        stat = safe_path.stat()
        file_info = {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "lines": len(content.splitlines()),
            "extension": safe_path.suffix
        }
        
        return {
            "success": True,
            "content": content,
            "file_info": file_info,
            "path": str(safe_path)
        }
    except Exception as e:
        return {"success": False, "error": f"Error reading file: {str(e)}"}


def write_file(file_path: str, content: str, create_directories: bool = True) -> Dict[str, Any]:
    """Write content to a file"""
    try:
        resolver = get_path_resolver()
        safe_path = resolver.safe_path(file_path)
        
        # Create parent directories if needed
        if create_directories:
            safe_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean up content - handle escaped newlines from malformed LLM output
        cleaned_content = content
        
        # Check if content contains literal \n instead of actual newlines
        if '\\n' in content and '\n' not in content:
            cleaned_content = content.replace('\\n', '\n')
        elif '\\n' in content and content.count('\\n') > content.count('\n'):
            cleaned_content = content.replace('\\n', '\n')
        
        # Also handle other common escape sequences
        cleaned_content = cleaned_content.replace('\\t', '\t')
        cleaned_content = cleaned_content.replace('\\"', '"')
        cleaned_content = cleaned_content.replace("\\'", "'")
        
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        stat = safe_path.stat()
        
        return {
            "success": True,
            "message": f"File written successfully: {file_path}",
            "path": str(safe_path),
            "size": stat.st_size,
            "lines": len(cleaned_content.splitlines()),
            "content_cleaned": cleaned_content != content
        }
    except Exception as e:
        return {"success": False, "error": f"Error writing file: {str(e)}"}


def edit_file_lines(file_path=None, edits=None, **kwargs) -> Dict[str, Any]:
    """Edit specific lines of a file.
    
    - If new_content is '', delete the line.
    - If new_content contains newlines, replace the line with multiple lines.
    - Accepts both 'edits' and 'lines' as the key for the edits dictionary.
    """
    # Extract file_path and edits from various argument formats
    if file_path is not None and edits is None and isinstance(file_path, dict):
        args = file_path
        file_path = args.get('file_path')
        edits = args.get('edits') or args.get('lines')
    
    if file_path is None or edits is None:
        file_path = kwargs.get('file_path', file_path)
        edits = kwargs.get('edits') or kwargs.get('lines') or edits
    
    if isinstance(edits, str):
        try:
            edits = json.loads(edits)
        except Exception:
            return {"error": "'edits' must be a dict or a JSON string representing a dict of line edits."}
    
    if not file_path or not isinstance(edits, dict):
        return {"error": "edit_file_lines requires 'file_path' (str) and 'edits' (dict) arguments."}
    
    try:
        expanded_path = os.path.expanduser(file_path)
        if not os.path.exists(expanded_path):
            return {"error": f"File not found: {file_path}"}
        
        with open(expanded_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Sort line numbers descending so edits don't affect subsequent indices
        edit_items = sorted(edits.items(), key=lambda x: int(x[0]), reverse=True)
        
        for line_num_str, new_content in edit_items:
            idx = int(line_num_str) - 1
            if 0 <= idx < len(lines):
                if new_content == '':
                    del lines[idx]
                elif '\n' in new_content:
                    new_lines = [l if l.endswith('\n') else l+'\n' for l in new_content.splitlines()]
                    lines[idx:idx+1] = new_lines
                else:
                    if lines[idx].endswith('\n') and not new_content.endswith('\n'):
                        new_content += '\n'
                    lines[idx] = new_content
        
        with open(expanded_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return {
            "success": True,
            "file_path": expanded_path,
            "lines_edited": list(edits.keys()),
            "total_lines": len(lines)
        }
    except Exception as e:
        logger.error(f"edit_file_lines error: {e}")
        return {"error": f"Failed to edit file lines: {str(e)}"}


# Tool definitions for OpenAI function calling
FILE_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string", 
                        "description": "Path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file (creates new file or overwrites existing)",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path where to write the file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "create_directories": {
                        "type": "boolean",
                        "description": "Whether to create parent directories if they don't exist",
                        "default": True
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file_lines",
            "description": "Edit specific lines of a file by line number",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to edit"
                    },
                    "edits": {
                        "type": "object",
                        "description": "Dictionary mapping line numbers (as strings) to new content. Empty string deletes the line.",
                        "additionalProperties": {"type": "string"}
                    },
                    "lines": {
                        "type": "object",
                        "description": "Alternative key for edits parameter",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["file_path"]
            }
        }
    }
]