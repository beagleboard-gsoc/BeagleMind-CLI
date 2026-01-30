"""
Permission Handler Module
Handles tool permission requests and user approvals
"""

import os
import json
from typing import Dict, Any

class PermissionHandler:
    """Handles tool permission requests and user interactions"""

    def __init__(self):
        pass

    def format_permission_request(self, function_name: str, function_args: Dict[str, Any]) -> str:
        """Format a detailed permission request for file operations"""

        if function_name == "write_file":
            file_path = function_args.get('file_path', 'Unknown')
            content = function_args.get('content', '')
            create_directories = function_args.get('create_directories', True)

            # Count lines and estimate size
            line_count = len(content.splitlines())
            content_size = len(content.encode('utf-8'))

            # Show preview of content (first 10 lines)
            content_lines = content.splitlines()
            preview_lines = content_lines[:10]
            preview = '\n'.join(preview_lines)
            if len(content_lines) > 10:
                preview += f"\n... (and {len(content_lines) - 10} more lines)"

            file_status = 'overwrite the existing file' if os.path.exists(os.path.expanduser(file_path)) else 'create a new file'

            permission_info = f"""Tool: write_file
Target: {file_path}
Size: {content_size} bytes ({line_count} lines)
Create Dirs: {'Yes' if create_directories else 'No'}

Content Preview:
{'-' * 40}
{preview[:500]}{'...' if len(preview) > 500 else ''}
{'-' * 40}

Note: This will {file_status}"""

            return permission_info

        elif function_name == "edit_file_lines":
            file_path = function_args.get('file_path', 'Unknown')
            edits = function_args.get('edits') or function_args.get('lines', {})

            permission_info = f"""Tool: edit_file_lines
Target: {file_path}
Lines to Modify: {len(edits)}

Proposed Changes:"""

            # Show details of each edit
            for line_num, new_content in sorted(edits.items(), key=lambda x: int(x[0])):
                if new_content == '':
                    permission_info += f"\n  Line {line_num}: DELETE this line"
                elif '\n' in new_content:
                    new_lines = new_content.splitlines()
                    permission_info += f"\n  Line {line_num}: REPLACE with {len(new_lines)} lines:"
                    for i, line in enumerate(new_lines[:3]):  # Show first 3 lines
                        permission_info += f"\n    {i+1}: {line[:60]}{'...' if len(line) > 60 else ''}"
                    if len(new_lines) > 3:
                        permission_info += f"\n    ... (and {len(new_lines) - 3} more lines)"
                else:
                    content_preview = new_content[:80] + ('...' if len(new_content) > 80 else '')
                    permission_info += f"\n  Line {line_num}: REPLACE with: {content_preview}"

            # Try to show existing content for context
            try:
                expanded_path = os.path.expanduser(file_path)
                if os.path.exists(expanded_path):
                    with open(expanded_path, 'r', encoding='utf-8', errors='ignore') as f:
                        existing_lines = f.readlines()

                    permission_info += f"\n\nCurrent Content (for context):"
                    for line_num in sorted(edits.keys(), key=int):
                        idx = int(line_num) - 1
                        if 0 <= idx < len(existing_lines):
                            current_content = existing_lines[idx].rstrip()[:80]
                            permission_info += f"\n  Line {line_num} (current): {current_content}{'...' if len(existing_lines[idx].rstrip()) > 80 else ''}"
                        else:
                            permission_info += f"\n  Line {line_num}: (line doesn't exist)"
                else:
                    permission_info += f"\n\nNote: File does not exist: {file_path}"
            except Exception:
                permission_info += f"\n\nNote: Could not read current file content"

            return permission_info

        else:
            # For other tools that might be added in the future
            return f"""Tool: {function_name}
Arguments: {json.dumps(function_args, indent=2)}"""

    def get_user_approval(self, permission_info: str) -> bool:
        """Get user approval for a tool operation - uses rich display from tool_display"""
        from ..cli.tool_display import tool_display
        
        tool_display.show_permission_request("Tool Permission", permission_info)

        while True:
            user_input = input("\nDo you approve this operation? (y/n): ").strip().lower()
            if user_input in ['y', 'yes']:
                return True
            elif user_input in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")


# Global instance
permission_handler = PermissionHandler()