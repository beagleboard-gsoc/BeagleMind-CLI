"""
Base utilities and path handling for tools.
"""

import os
import socket
import platform
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_machine_info() -> Dict[str, Any]:
    """Get information about the current machine"""
    try:
        return {
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn(),
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "user": os.getenv('USER', os.getenv('USERNAME', 'unknown')),
            "home": str(Path.home()),
            "cwd": str(Path.cwd())
        }
    except Exception as e:
        logger.warning(f"Could not get full machine info: {e}")
        return {
            "hostname": "unknown",
            "os": platform.system(),
            "user": os.getenv('USER', 'unknown'),
            "cwd": str(Path.cwd())
        }


class PathResolver:
    """Handles path resolution and safety"""
    
    def __init__(self, base_directory: Optional[str] = None):
        if base_directory is None:
            self.base_directory = Path.cwd()
        else:
            self.base_directory = Path(base_directory)
        self.base_directory.mkdir(exist_ok=True)
        self.current_working_directory = Path.cwd()
    
    def safe_path(self, path: str) -> Path:
        """Convert string path to safe Path object, handle relative paths"""
        path_obj = Path(path)
        if not path_obj.is_absolute():
            # Check if file exists in current working directory first
            cwd_path = self.current_working_directory / path_obj
            if cwd_path.exists():
                return cwd_path.resolve()
            # Otherwise, check base directory
            base_path = self.base_directory / path_obj
            if base_path.exists():
                return base_path.resolve()
            # If neither exists, default to current working directory for new files
            return cwd_path.resolve()
        return path_obj.resolve()


# Shared path resolver instance
_path_resolver: Optional[PathResolver] = None


def get_path_resolver(base_directory: Optional[str] = None) -> PathResolver:
    """Get or create shared path resolver"""
    global _path_resolver
    if _path_resolver is None or base_directory is not None:
        _path_resolver = PathResolver(base_directory)
    return _path_resolver