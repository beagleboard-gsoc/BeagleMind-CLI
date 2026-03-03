"""
BeagleMind Tools Registry - Modular tool system.

This module provides a unified interface for all available tools.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from .base import get_path_resolver, get_machine_info as base_get_machine_info
from .file_tools import (
    read_file, write_file, edit_file_lines,
    FILE_TOOL_DEFINITIONS
)
from .directory_tools import (
    list_directory, search_in_files, show_directory_tree,
    DIRECTORY_TOOL_DEFINITIONS
)
from .system_tools import (
    get_machine_info, run_command,
    SYSTEM_TOOL_DEFINITIONS
)
from .code_tools import (
    analyze_code,
    CODE_TOOL_DEFINITIONS
)
from .retrieval_tools import (
    retrieve_context,
    RETRIEVAL_TOOL_DEFINITIONS
)

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Unified tool registry with all available tools"""
    
    def __init__(self, base_directory: Optional[str] = None):
        """Initialize the tool registry with optional base directory"""
        self._resolver = get_path_resolver(base_directory)
        self._machine_info = base_get_machine_info()
        
        # Map tool names to their functions
        self._tools = {
            "read_file": read_file,
            "write_file": write_file,
            "edit_file_lines": edit_file_lines,
            "list_directory": list_directory,
            "search_in_files": search_in_files,
            "show_directory_tree": show_directory_tree,
            "get_machine_info": get_machine_info,
            "run_command": run_command,
            "analyze_code": analyze_code,
            "retrieve_context": retrieve_context,
        }
        
        logger.info(f"Tool registry initialized on {self._machine_info['hostname']}")
    
    @property
    def base_directory(self):
        return self._resolver.base_directory
    
    @property
    def current_working_directory(self):
        return self._resolver.current_working_directory
    
    @property
    def machine_info(self):
        return self._machine_info
    
    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return OpenAI function definitions for all tools"""
        definitions = []
        definitions.extend(FILE_TOOL_DEFINITIONS)
        definitions.extend(DIRECTORY_TOOL_DEFINITIONS)
        definitions.extend(SYSTEM_TOOL_DEFINITIONS)
        definitions.extend(CODE_TOOL_DEFINITIONS)
        definitions.extend(RETRIEVAL_TOOL_DEFINITIONS)
        return definitions
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with given arguments"""
        if tool_name not in self._tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            return self._tools[tool_name](**kwargs)
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return {"success": False, "error": f"Tool execution error: {str(e)}"}

# Create default global instance
tool_registry = ToolRegistry()

# For backward compatibility - alias to old name
OptimizedToolRegistry = ToolRegistry
enhanced_tool_registry_optimized = tool_registry

__all__ = [
    "ToolRegistry", "tool_registry", "enhanced_tool_registry_optimized",
    "retrieve_context", "RETRIEVAL_TOOL_DEFINITIONS"
]