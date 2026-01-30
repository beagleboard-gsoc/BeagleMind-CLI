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
        }
        
        logger.info(f"Tool registry initialized on {self._machine_info['hostname']}")
        logger.info(f"Current working directory: {self._resolver.current_working_directory}")
        logger.info(f"Base directory: {self._resolver.base_directory}")
    
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
    
    def parse_tool_calls(self, tool_calls) -> List[Dict[str, Any]]:
        """Parse and execute tool calls from OpenAI function calling"""
        results = []
        
        for tool_call in tool_calls:
            try:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                result = self.execute_tool(function_name, **arguments)
                
                results.append({
                    "tool_call_id": tool_call.id,
                    "function_name": function_name,
                    "result": result
                })
                
            except Exception as e:
                results.append({
                    "tool_call_id": tool_call.id,
                    "function_name": getattr(tool_call.function, 'name', 'unknown'),
                    "result": {"success": False, "error": f"Tool execution error: {str(e)}"}
                })
        
        return results
    
    # Convenience methods that delegate to individual tools
    def read_file(self, file_path: str) -> Dict[str, Any]:
        return read_file(file_path)
    
    def write_file(self, file_path: str, content: str, create_directories: bool = True) -> Dict[str, Any]:
        return write_file(file_path, content, create_directories)
    
    def edit_file_lines(self, file_path=None, edits=None, **kwargs) -> Dict[str, Any]:
        return edit_file_lines(file_path, edits, **kwargs)
    
    def list_directory(self, directory: str, show_hidden: bool = False, 
                       file_extensions: Optional[List[str]] = None, 
                       recursive: bool = False) -> Dict[str, Any]:
        return list_directory(directory, show_hidden, file_extensions, recursive)
    
    def search_in_files(self, directory: str, pattern: str, 
                        file_extensions: Optional[List[str]] = None, 
                        is_regex: bool = False) -> Dict[str, Any]:
        return search_in_files(directory, pattern, file_extensions, is_regex)
    
    def show_directory_tree(self, directory: str, max_depth: int = 3, 
                            show_hidden: bool = False, 
                            files_only: bool = False) -> Dict[str, Any]:
        return show_directory_tree(directory, max_depth, show_hidden, files_only)
    
    def get_machine_info(self) -> Dict[str, Any]:
        return get_machine_info()
    
    def run_command(self, command: str, working_directory: Optional[str] = None, 
                    timeout: int = 30) -> Dict[str, Any]:
        return run_command(command, working_directory, timeout)
    
    def analyze_code(self, file_path: str, language: Optional[str] = None, 
                     check_ros_patterns: bool = True) -> Dict[str, Any]:
        return analyze_code(file_path, language, check_ros_patterns)


# Create default global instance
tool_registry = ToolRegistry()

# For backward compatibility - alias to old name
OptimizedToolRegistry = ToolRegistry
enhanced_tool_registry_optimized = tool_registry

__all__ = [
    # Classes
    "ToolRegistry",
    "OptimizedToolRegistry",
    
    # Instances
    "tool_registry",
    "enhanced_tool_registry_optimized",
    
    # Functions
    "read_file",
    "write_file",
    "edit_file_lines",
    "list_directory",
    "search_in_files",
    "show_directory_tree",
    "get_machine_info",
    "run_command",
    "analyze_code",
    
    # Tool definitions
    "FILE_TOOL_DEFINITIONS",
    "DIRECTORY_TOOL_DEFINITIONS",
    "SYSTEM_TOOL_DEFINITIONS",
    "CODE_TOOL_DEFINITIONS",
]