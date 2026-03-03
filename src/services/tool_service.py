"""
Tool Service Module
Handles tool execution and management
"""

import json
import logging
import re
from typing import Dict, Any, List

from ..tools_registry import enhanced_tool_registry_optimized as tool_registry

logger = logging.getLogger(__name__)

# Lazy import for tool_display to avoid circular import
_tool_display = None

def get_tool_display():
    """Lazy import of tool_display to avoid circular imports"""
    global _tool_display
    if _tool_display is None:
        from ..cli.tool_display import tool_display
        _tool_display = tool_display
    return _tool_display


class ToolService:
    """Service for handling tool execution and management"""

    def __init__(self):
        pass

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return the OpenAI function definitions for all available tools"""
        return tool_registry.get_all_tool_definitions()

    def execute_tool(self, function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function by name with given arguments"""
        try:
            # Delegate completely to the registry
            return tool_registry.execute_tool(function_name, **function_args)
        except Exception as e:
            return {"success": False, "error": f"Tool execution error: {str(e)}"}

    def execute_tool_with_feedback(self, function_name: str, function_args: Dict[str, Any], 
                                  auto_approve: bool = False) -> Dict[str, Any]:
        """Execute a tool with permission checking and user feedback"""
        from ..helpers.permission_handler import permission_handler
        
        requires_permission = function_name in ["write_file", "edit_file_lines"]
        
        # Retrieval does not require permission
        if function_name == "retrieve_context":
            requires_permission = False

        user_approved = auto_approve
        display = get_tool_display()
        
        if requires_permission and not auto_approve:
            permission_info = permission_handler.format_permission_request(function_name, function_args)
            display.show_permission_request(function_name, permission_info)
            
            while True:
                user_input = input("\nDo you approve this operation? (y/n): ").strip().lower()
                if user_input in ['y', 'yes']:
                    user_approved = True
                    break
                elif user_input in ['n', 'no']:
                    user_approved = False
                    break
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
        
        if user_approved or not requires_permission:
            tool_result = self.execute_tool(function_name, function_args)
            display.show_tool_result(function_name, function_args, tool_result)
            return {
                "result": tool_result,
                "requires_permission": requires_permission,
                "user_approved": user_approved if requires_permission else None
            }
        else:
            display.show_operation_cancelled()
            return {
                "result": {"success": False, "error": "Operation cancelled by user", "user_denied": True},
                "requires_permission": requires_permission,
                "user_approved": False
            }

    def parse_tool_arguments(self, args_str: str, function_name: str) -> Dict[str, Any]:
        """Parse tool arguments from potentially malformed JSON"""
        import re
        import json
        
        try:
            return json.loads(args_str)
        except json.JSONDecodeError:
            if function_name == "run_command":
                return self._parse_command_arguments(args_str)
            elif function_name == "write_file":
                return self._parse_write_file_arguments(args_str)
            else:
                return self._parse_generic_arguments(args_str)
    
    def _parse_command_arguments(self, args_str: str) -> Dict[str, Any]:
        """Parse command arguments from malformed JSON"""
        patterns = [
            r'"command":\s*"([^"]*)"',  # Standard pattern
            r'"command":\s*"([^"]*?)(?:"|$)',  # Pattern allowing unclosed quotes
            r'"command":\s*([^,}]*)',  # Pattern without quotes
        ]
        
        for pattern in patterns:
            command_match = re.search(pattern, args_str, re.DOTALL)
            if command_match:
                command = command_match.group(1).strip()
                command = ' '.join(command.split())
                return {"command": command}
        
        # Extract anything that looks like a command
        lines = args_str.split('\n')
        for line in lines:
            if 'command' in line.lower():
                cleaned = re.sub(r'[^a-zA-Z0-9\s\-\.\/_><=;]', ' ', line)
                if cleaned.strip():
                    return {"command": "echo 'Extracted: " + cleaned.strip()[:50] + "'"}
        
        return {"command": "echo 'Could not parse command'"}
    
    def _parse_write_file_arguments(self, args_str: str) -> Dict[str, Any]:
        """Parse write_file arguments from malformed JSON"""
        file_path_match = re.search(r'"file_path":\s*"([^"]*)"', args_str)
        content_match = re.search(r'"content":\s*"([^"]*)"', args_str, re.DOTALL)
        
        file_path = file_path_match.group(1) if file_path_match else "recovered_file.txt"
        content = content_match.group(1) if content_match else "# Content could not be recovered"
        
        return {
            "file_path": file_path,
            "content": content
        }
    
    def _parse_generic_arguments(self, args_str: str) -> Dict[str, Any]:
        """Parse generic arguments from malformed JSON"""
        try:
            cleaned_args = re.sub(r'[\n\r\t]', ' ', args_str)
            cleaned_args = re.sub(r'\s+', ' ', cleaned_args)
            return json.loads(cleaned_args)
        except:
            return {}


# Global instance
tool_service = ToolService()