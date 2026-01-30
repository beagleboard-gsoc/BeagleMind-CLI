"""
Tool display formatting using Rich library.
Provides clean, professional output for tool execution results.
"""

from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED

console = Console()


class ToolDisplay:
    """Handles rich display formatting for tool operations"""
    
    @staticmethod
    def show_permission_request(function_name: str, permission_info: str):
        """Display a permission request panel"""
        title = f"Tool Request: {function_name}"
        panel = Panel(
            permission_info,
            title=title,
            title_align="left",
            border_style="yellow",
            box=ROUNDED
        )
        console.print()
        console.print(panel)
    
    @staticmethod
    def show_operation_cancelled():
        """Display operation cancelled message"""
        console.print()
        console.print("[bold red]Operation cancelled by user[/bold red]")
    
    @staticmethod
    def show_tool_result(function_name: str, function_args: Dict[str, Any], tool_result: Dict[str, Any]):
        """Display tool execution result with rich formatting"""
        success = tool_result.get("success", False)
        
        if success:
            ToolDisplay._show_success_result(function_name, function_args, tool_result)
        else:
            ToolDisplay._show_failure_result(function_name, tool_result)
    
    @staticmethod
    def _show_success_result(function_name: str, function_args: Dict[str, Any], tool_result: Dict[str, Any]):
        """Display successful tool execution"""
        # Create a table for the result details
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        if function_name == "write_file":
            file_path = function_args.get('file_path', 'Unknown')
            content_size = len(function_args.get('content', ''))
            table.add_row("File", file_path)
            table.add_row("Size", f"{content_size} bytes")
            table.add_row("Status", "[green]Written[/green]")
        
        elif function_name == "edit_file_lines":
            file_path = function_args.get('file_path', 'Unknown')
            edits = function_args.get('edits', {})
            table.add_row("File", file_path)
            table.add_row("Lines Modified", str(len(edits)))
            table.add_row("Status", "[green]Edited[/green]")
        
        elif function_name == "read_file":
            file_path = function_args.get('file_path', 'Unknown')
            content_size = len(tool_result.get('content', ''))
            table.add_row("File", file_path)
            table.add_row("Size", f"{content_size} bytes")
            table.add_row("Status", "[green]Read[/green]")
        
        elif function_name == "run_command":
            command = function_args.get('command', '')
            return_code = tool_result.get('return_code', 'N/A')
            cmd_display = command[:60] + '...' if len(command) > 60 else command
            table.add_row("Command", cmd_display)
            table.add_row("Exit Code", str(return_code))
            status_color = "green" if return_code == 0 else "yellow"
            table.add_row("Status", f"[{status_color}]Completed[/{status_color}]")
        
        elif function_name == "search_in_files":
            pattern = function_args.get('pattern', '')
            results = tool_result.get('results', [])
            files_searched = tool_result.get('files_searched', 0)
            table.add_row("Pattern", f"'{pattern}'")
            table.add_row("Files Searched", str(files_searched))
            table.add_row("Matches Found", f"{len(results)} files")
        
        elif function_name == "show_directory_tree":
            directory = function_args.get('directory', 'Unknown')
            summary = tool_result.get('summary', {})
            max_depth = function_args.get('max_depth', 3)
            table.add_row("Directory", directory)
            table.add_row("Depth", f"{max_depth} levels")
            table.add_row("Contents", f"{summary.get('directories', 0)} dirs, {summary.get('files', 0)} files")
        
        elif function_name == "analyze_code":
            file_path = function_args.get('file_path', 'Unknown')
            language = tool_result.get('language', 'Unknown')
            line_count = tool_result.get('line_count', 0)
            table.add_row("File", file_path)
            table.add_row("Language", language)
            table.add_row("Lines", str(line_count))
        
        else:
            table.add_row("Status", "[green]Completed[/green]")
        
        panel = Panel(
            table,
            title=f"[bold green]Tool: {function_name}[/bold green]",
            title_align="left",
            border_style="green",
            box=ROUNDED
        )
        console.print()
        console.print(panel)
    
    @staticmethod
    def _show_failure_result(function_name: str, tool_result: Dict[str, Any]):
        """Display failed tool execution"""
        error_msg = tool_result.get('error', 'Unknown error')
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Error", f"[red]{error_msg}[/red]")
        
        panel = Panel(
            table,
            title=f"[bold red]Tool Failed: {function_name}[/bold red]",
            title_align="left",
            border_style="red",
            box=ROUNDED
        )
        console.print()
        console.print(panel)
    
    @staticmethod
    def show_tools_summary(tool_results: list):
        """Display a summary table of all tools used"""
        if not tool_results:
            return
        
        table = Table(
            title="Tools Executed",
            box=ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Tool", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Details", style="dim")
        
        for result in tool_results:
            tool_name = result.get('tool', 'Unknown')
            tool_result = result.get('result', {})
            success = tool_result.get('success', False)
            
            status = Text("Success", style="green") if success else Text("Failed", style="red")
            
            # Generate details preview
            if success:
                details = ToolDisplay._get_result_preview(tool_name, result.get('arguments', {}), tool_result)
            else:
                details = tool_result.get('error', 'Unknown error')[:40]
            
            table.add_row(tool_name, status, details)
        
        console.print()
        console.print(table)
    
    @staticmethod
    def _get_result_preview(function_name: str, function_args: Dict[str, Any], tool_result: Dict[str, Any]) -> str:
        """Generate a short preview of the result"""
        if function_name == "write_file":
            return function_args.get('file_path', '')[:40]
        elif function_name == "edit_file_lines":
            return function_args.get('file_path', '')[:40]
        elif function_name == "read_file":
            return function_args.get('file_path', '')[:40]
        elif function_name == "run_command":
            return function_args.get('command', '')[:40]
        elif function_name == "search_in_files":
            return f"Pattern: {function_args.get('pattern', '')[:20]}"
        elif function_name == "show_directory_tree":
            return function_args.get('directory', '')[:40]
        elif function_name == "analyze_code":
            return function_args.get('file_path', '')[:40]
        else:
            return "Completed"


# Singleton instance
tool_display = ToolDisplay()