"""
Directory and search tools: list, search, tree operations.
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import get_path_resolver

logger = logging.getLogger(__name__)


def list_directory(directory: str, show_hidden: bool = False, 
                   file_extensions: Optional[List[str]] = None, 
                   recursive: bool = False) -> Dict[str, Any]:
    """List directory contents with filtering"""
    try:
        resolver = get_path_resolver()
        safe_dir = resolver.safe_path(directory)
        
        if not safe_dir.exists():
            return {"success": False, "error": f"Directory not found: {directory}"}
        
        if not safe_dir.is_dir():
            return {"success": False, "error": f"Path is not a directory: {directory}"}
        
        items = []
        paths = safe_dir.rglob('*') if recursive else safe_dir.iterdir()
        
        for path in paths:
            if not show_hidden and path.name.startswith('.'):
                continue
            
            if file_extensions and path.is_file() and path.suffix.lower() not in [ext.lower() for ext in file_extensions]:
                continue
            
            stat_info = path.stat()
            item = {
                "name": path.name,
                "path": str(path),
                "relative_path": str(path.relative_to(safe_dir)),
                "type": "directory" if path.is_dir() else "file",
                "size": stat_info.st_size if path.is_file() else None,
                "modified": stat_info.st_mtime,
                "permissions": oct(stat_info.st_mode)[-3:]
            }
            
            if path.is_file():
                item["extension"] = path.suffix
            
            items.append(item)
        
        items.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
        
        return {
            "success": True,
            "directory": str(safe_dir),
            "total_items": len(items),
            "directories": len([i for i in items if i["type"] == "directory"]),
            "files": len([i for i in items if i["type"] == "file"]),
            "items": items
        }
    except Exception as e:
        return {"success": False, "error": f"Error listing directory: {str(e)}"}


def search_in_files(directory: str, pattern: str, 
                    file_extensions: Optional[List[str]] = None, 
                    is_regex: bool = False) -> Dict[str, Any]:
    """Search for text patterns in files"""
    try:
        resolver = get_path_resolver()
        safe_dir = resolver.safe_path(directory)
        
        if not safe_dir.exists():
            return {"success": False, "error": f"Directory not found: {directory}"}
        
        if not safe_dir.is_dir():
            return {"success": False, "error": f"Path is not a directory: {directory}"}
        
        if is_regex:
            try:
                regex_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            except re.error as e:
                return {"success": False, "error": f"Invalid regex pattern: {str(e)}"}
        else:
            regex_pattern = re.compile(re.escape(pattern), re.IGNORECASE | re.MULTILINE)
        
        results = []
        files_searched = 0
        
        for file_path in safe_dir.rglob('*'):
            if not file_path.is_file():
                continue
            
            if file_extensions and file_path.suffix.lower() not in [ext.lower() for ext in file_extensions]:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                files_searched += 1
                matches = []
                
                for line_num, line in enumerate(content.splitlines(), 1):
                    if regex_pattern.search(line):
                        matches.append({
                            "line_number": line_num,
                            "line_content": line.strip(),
                            "match_positions": [m.span() for m in regex_pattern.finditer(line)]
                        })
                
                if matches:
                    results.append({
                        "file_path": str(file_path),
                        "relative_path": str(file_path.relative_to(safe_dir)),
                        "file_size": file_path.stat().st_size,
                        "match_count": len(matches),
                        "matches": matches[:10]
                    })
            
            except (UnicodeDecodeError, PermissionError):
                continue
        
        return {
            "success": True,
            "pattern": pattern,
            "is_regex": is_regex,
            "directory": str(safe_dir),
            "files_searched": files_searched,
            "files_with_matches": len(results),
            "results": results[:50]
        }
    except Exception as e:
        return {"success": False, "error": f"Error searching files: {str(e)}"}


def show_directory_tree(directory: str, max_depth: int = 3, 
                        show_hidden: bool = False, 
                        files_only: bool = False) -> Dict[str, Any]:
    """Show directory structure using tree command"""
    try:
        resolver = get_path_resolver()
        safe_dir = resolver.safe_path(directory)
        
        if not safe_dir.exists():
            return {"success": False, "error": f"Directory not found: {directory}"}
        
        if not safe_dir.is_dir():
            return {"success": False, "error": f"Path is not a directory: {directory}"}
        
        cmd_parts = ["tree", "-L", str(max_depth)]
        
        if show_hidden:
            cmd_parts.append("-a")
        if files_only:
            cmd_parts.append("-f")
        
        cmd_parts.append(str(safe_dir))
        
        result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return _fallback_directory_tree(safe_dir, max_depth, show_hidden)
        
        output_lines = result.stdout.strip().split('\n')
        summary_line = output_lines[-1] if output_lines else ""
        
        directories = 0
        files = 0
        if "directories" in summary_line and "files" in summary_line:
            dir_match = re.search(r'(\d+)\s+directories', summary_line)
            file_match = re.search(r'(\d+)\s+files', summary_line)
            if dir_match:
                directories = int(dir_match.group(1))
            if file_match:
                files = int(file_match.group(1))
        
        return {
            "success": True,
            "directory": str(safe_dir),
            "tree_output": result.stdout,
            "max_depth": max_depth,
            "show_hidden": show_hidden,
            "files_only": files_only,
            "summary": {
                "directories": directories,
                "files": files,
                "total_items": directories + files
            }
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Tree command timed out"}
    except Exception as e:
        return {"success": False, "error": f"Error showing directory tree: {str(e)}"}


def _fallback_directory_tree(directory: Path, max_depth: int, show_hidden: bool) -> Dict[str, Any]:
    """Fallback directory tree when tree command is unavailable"""
    try:
        tree_lines = []
        
        def build_tree(path: Path, prefix: str = "", depth: int = 0):
            if depth >= max_depth:
                return
            
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for i, item in enumerate(items):
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir() and depth < max_depth - 1:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    build_tree(item, next_prefix, depth + 1)
        
        tree_lines.insert(0, str(directory))
        build_tree(directory)
        
        all_items = list(directory.rglob('*'))
        if not show_hidden:
            all_items = [item for item in all_items if not any(part.startswith('.') for part in item.parts)]
        
        directories = len([item for item in all_items if item.is_dir()])
        files = len([item for item in all_items if item.is_file()])
        
        tree_output = '\n'.join(tree_lines)
        tree_output += f"\n\n{directories} directories, {files} files"
        
        return {
            "success": True,
            "directory": str(directory),
            "tree_output": tree_output,
            "max_depth": max_depth,
            "show_hidden": show_hidden,
            "fallback_used": True,
            "summary": {
                "directories": directories,
                "files": files,
                "total_items": directories + files
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error in fallback tree: {str(e)}"}


# Tool definitions for OpenAI function calling
DIRECTORY_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_in_files",
            "description": "Search for text patterns in files within a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Text pattern to search for (supports regex)"
                    },
                    "file_extensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File extensions to include in search (e.g., ['.py', '.cpp'])"
                    },
                    "is_regex": {
                        "type": "boolean",
                        "description": "Whether the pattern is a regex",
                        "default": False
                    }
                },
                "required": ["directory", "pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_directory_tree",
            "description": "Show directory structure using tree command",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to show tree structure for"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to show (default: 3)",
                        "default": 3
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Whether to show hidden files",
                        "default": False
                    },
                    "files_only": {
                        "type": "boolean",
                        "description": "Show only files, not directories",
                        "default": False
                    }
                },
                "required": ["directory"]
            }
        }
    }
]