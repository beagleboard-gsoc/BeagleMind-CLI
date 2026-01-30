"""
Code analysis tools: syntax checking, style analysis.
"""

import ast
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import get_path_resolver

logger = logging.getLogger(__name__)


def analyze_code(file_path: str, language: Optional[str] = None, 
                 check_ros_patterns: bool = True) -> Dict[str, Any]:
    """Analyze code for syntax errors and best practices"""
    try:
        resolver = get_path_resolver()
        safe_path = resolver.safe_path(file_path)
        
        if not safe_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        if not language:
            language = _detect_language(safe_path)
        
        analysis_result = {
            "file_path": str(safe_path),
            "language": language,
            "file_size": len(content),
            "line_count": len(content.splitlines()),
            "syntax_errors": [],
            "style_issues": [],
            "ros_issues": [],
            "suggestions": []
        }
        
        if language == "python":
            analysis_result.update(_analyze_python_code(content, check_ros_patterns))
        elif language == "cpp":
            analysis_result.update(_analyze_cpp_code(content, check_ros_patterns))
        else:
            analysis_result["suggestions"].append(f"Code analysis not available for language: {language}")
        
        return {"success": True, **analysis_result}
    except Exception as e:
        return {"success": False, "error": f"Error analyzing code: {str(e)}"}


def _detect_language(file_path: Path) -> str:
    """Detect programming language from file extension"""
    extension_map = {
        '.py': 'python',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c': 'c',
        '.h': 'cpp',
        '.hpp': 'cpp',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.rs': 'rust',
        '.go': 'go',
        '.rb': 'ruby',
        '.sh': 'bash',
        '.bash': 'bash',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.launch': 'xml',
        '.msg': 'ros_msg',
        '.srv': 'ros_srv',
        '.action': 'ros_action'
    }
    return extension_map.get(file_path.suffix.lower(), 'unknown')


def _analyze_python_code(content: str, check_ros: bool = True) -> Dict[str, Any]:
    """Analyze Python code for syntax errors and style issues"""
    result = {
        "syntax_errors": [],
        "style_issues": [],
        "ros_issues": [],
        "suggestions": []
    }
    
    # Check syntax
    try:
        ast.parse(content)
    except SyntaxError as e:
        result["syntax_errors"].append({
            "line": e.lineno,
            "column": e.offset,
            "message": str(e.msg),
            "text": e.text.strip() if e.text else ""
        })
    
    lines = content.splitlines()
    
    # Style checks
    for i, line in enumerate(lines, 1):
        # Line length
        if len(line) > 120:
            result["style_issues"].append({
                "line": i,
                "issue": f"Line too long ({len(line)} > 120 characters)"
            })
        
        # Trailing whitespace
        if line.rstrip() != line:
            result["style_issues"].append({
                "line": i,
                "issue": "Trailing whitespace"
            })
        
        # Tab/space mixing
        if '\t' in line and '    ' in line:
            result["style_issues"].append({
                "line": i,
                "issue": "Mixed tabs and spaces"
            })
    
    # ROS-specific checks
    if check_ros:
        ros_patterns = [
            (r'rospy\.init_node\([^)]+,\s*anonymous\s*=\s*False\)', 
             "Consider using anonymous=True for nodes that can run multiple instances"),
            (r'rospy\.spin\(\)', 
             "Consider using rospy.Rate() for controlled loop frequency instead of blocking spin"),
            (r'from\s+std_msgs\.msg\s+import\s+\*', 
             "Avoid wildcard imports for ROS messages, import specific types"),
            (r'rospy\.loginfo\([^)]*%[^)]*\)', 
             "Consider using rospy.loginfo with format strings instead of % formatting")
        ]
        
        for pattern, suggestion in ros_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    result["ros_issues"].append({
                        "line": i,
                        "suggestion": suggestion
                    })
    
    # General suggestions
    if 'import rospy' in content and 'if __name__' not in content:
        result["suggestions"].append("Consider adding 'if __name__ == \"__main__\":' guard")
    
    if 'import rospy' in content and 'try:' not in content:
        result["suggestions"].append("Consider wrapping main code in try/except for graceful shutdown")
    
    return result


def _analyze_cpp_code(content: str, check_ros: bool = True) -> Dict[str, Any]:
    """Analyze C++ code for common issues"""
    result = {
        "syntax_errors": [],
        "style_issues": [],
        "ros_issues": [],
        "suggestions": []
    }
    
    lines = content.splitlines()
    
    # Basic syntax checks
    brace_count = 0
    paren_count = 0
    bracket_count = 0
    
    for i, line in enumerate(lines, 1):
        # Count brackets
        brace_count += line.count('{') - line.count('}')
        paren_count += line.count('(') - line.count(')')
        bracket_count += line.count('[') - line.count(']')
        
        # Line length
        if len(line) > 120:
            result["style_issues"].append({
                "line": i,
                "issue": f"Line too long ({len(line)} > 120 characters)"
            })
        
        # Trailing whitespace
        if line.rstrip() != line:
            result["style_issues"].append({
                "line": i,
                "issue": "Trailing whitespace"
            })
    
    # Check for unbalanced brackets
    if brace_count != 0:
        result["syntax_errors"].append({
            "line": len(lines),
            "message": f"Unbalanced braces: {'+' if brace_count > 0 else ''}{brace_count}"
        })
    
    if paren_count != 0:
        result["syntax_errors"].append({
            "line": len(lines),
            "message": f"Unbalanced parentheses: {'+' if paren_count > 0 else ''}{paren_count}"
        })
    
    # ROS-specific checks
    if check_ros:
        ros_patterns = [
            (r'ros::spin\(\)', 
             "Consider using ros::spinOnce() with a ros::Rate for controlled loop frequency"),
            (r'#include\s*<ros/ros\.h>', 
             "For ROS2, use rclcpp instead of ros.h"),
            (r'ros::NodeHandle\s+nh\s*;', 
             "Consider using private node handle for parameters: ros::NodeHandle nh(\"~\")")
        ]
        
        for pattern, suggestion in ros_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    result["ros_issues"].append({
                        "line": i,
                        "suggestion": suggestion
                    })
    
    # General suggestions
    if '#include' in content and '#pragma once' not in content and '#ifndef' not in content:
        if content.strip().startswith('#include') or any('.h' in line for line in lines[:5]):
            result["suggestions"].append("Consider adding header guards (#pragma once or #ifndef)")
    
    return result


# Tool definitions for OpenAI function calling
CODE_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_code",
            "description": "Analyze code for syntax errors, style issues, and ROS best practices",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["python", "cpp"],
                        "description": "Programming language of the file"
                    },
                    "check_ros_patterns": {
                        "type": "boolean",
                        "description": "Whether to check for ROS-specific patterns and best practices",
                        "default": True
                    }
                },
                "required": ["file_path"]
            }
        }
    }
]