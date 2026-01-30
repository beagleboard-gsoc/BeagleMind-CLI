"""
BeagleMind Tool Registry - Backward compatible wrapper.

This module re-exports from the modular tools package for backward compatibility.
For new code, import directly from src.tools instead.
"""

from .tools import (
    ToolRegistry,
    OptimizedToolRegistry,
    tool_registry,
    enhanced_tool_registry_optimized,
    
    # Individual tool functions
    read_file,
    write_file,
    edit_file_lines,
    list_directory,
    search_in_files,
    show_directory_tree,
    get_machine_info,
    run_command,
    analyze_code,
    
    # Tool definitions
    FILE_TOOL_DEFINITIONS,
    DIRECTORY_TOOL_DEFINITIONS,
    SYSTEM_TOOL_DEFINITIONS,
    CODE_TOOL_DEFINITIONS,
)

from .tools.base import get_path_resolver, PathResolver

__all__ = [
    # Classes
    "ToolRegistry",
    "OptimizedToolRegistry",
    "PathResolver",
    
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
    "get_path_resolver",
    
    # Tool definitions
    "FILE_TOOL_DEFINITIONS",
    "DIRECTORY_TOOL_DEFINITIONS",
    "SYSTEM_TOOL_DEFINITIONS",
    "CODE_TOOL_DEFINITIONS",
]
