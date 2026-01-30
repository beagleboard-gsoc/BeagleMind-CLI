"""
System tools: command execution, machine info.
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .base import get_path_resolver, get_machine_info as _get_machine_info

logger = logging.getLogger(__name__)


def get_machine_info() -> Dict[str, Any]:
    """Return machine information for the current system"""
    resolver = get_path_resolver()
    machine_info = _get_machine_info()
    
    return {
        "success": True,
        "machine_info": machine_info,
        "current_working_directory": str(resolver.current_working_directory),
        "base_directory": str(resolver.base_directory),
        "environment": {
            "PATH": os.getenv('PATH', ''),
            "HOME": os.getenv('HOME', ''),
            "USER": os.getenv('USER', ''),
            "SHELL": os.getenv('SHELL', ''),
            "PWD": os.getenv('PWD', str(resolver.current_working_directory))
        }
    }


def run_command(command: str, working_directory: Optional[str] = None, 
                timeout: int = 30) -> Dict[str, Any]:
    """Execute a shell command"""
    try:
        resolver = get_path_resolver()
        
        if working_directory:
            work_dir = resolver.safe_path(working_directory)
            if not work_dir.exists():
                return {"success": False, "error": f"Working directory not found: {working_directory}"}
        else:
            work_dir = resolver.current_working_directory
        
        # Security check - prevent dangerous commands
        dangerous_patterns = [
            r'\brm\s+-rf\s+/',
            r'\bdd\s+if=',
            r'\bformat\s+',
            r'\bmkfs\.',
            r'\bshutdown',
            r'\breboot',
            r'\bhalt',
            r'>\s*/dev/',
            r'\bsudo\s+rm',
            r'\bsudo\s+dd'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {"success": False, "error": f"Command blocked for security reasons: {command}"}
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "success": True,
            "command": command,
            "working_directory": str(work_dir),
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success_execution": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout} seconds"}
    except Exception as e:
        return {"success": False, "error": f"Error executing command: {str(e)}"}


# Tool definitions for OpenAI function calling
SYSTEM_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_machine_info",
            "description": "Get information about the current machine including hostname, OS, user, and working directory",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command and return the output",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Working directory for the command",
                        "default": None
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        }
    }
]