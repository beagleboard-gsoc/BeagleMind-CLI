"""
Display and output formatting for BeagleMind CLI.
"""

from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.spinner import Spinner
from rich.live import Live
import time

console = Console()


class DisplayManager:
    """Handles all display and output formatting"""

    def show_models_table(self, table_data: List[Dict[str, Any]], config_info: Dict[str, Any]):
        """Display models table with configuration info"""
        table = Table(title="Available BeagleMind Models")
        table.add_column("Backend", style="cyan", no_wrap=True)
        table.add_column("Model Name", style="magenta")
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")

        for row in table_data:
            table.add_row(
                row["backend"],
                row["model"],
                row["type"],
                row["status"]
            )

        console.print(table)

        # Show current default settings
        current_panel = Panel(
            f"Current Defaults:\n"
            f"Backend: [cyan]{config_info['backend']}[/cyan]\n"
            f"Model: [magenta]{config_info['model']}[/magenta]\n"
            f"Temperature: [yellow]{config_info['temperature']}[/yellow]",
            title="Current Configuration",
            border_style="blue"
        )
        console.print(current_panel)

    def show_warning(self, message: str):
        """Show warning message"""
        console.print(f"[yellow]{message}[/yellow]")

    def show_error(self, message: str):
        """Show error message"""
        console.print(f"[red]{message}[/red]")

    def show_success(self, message: str):
        """Show success message"""
        console.print(f"[green]{message}[/green]")

    def show_spinner(self, message: str):
        """Create a spinner context manager"""
        return console.status(f"[bold green]{message}")

    def show_chat_response(self, result: Dict[str, Any], show_sources: bool = False):
        """Display chat response with all components"""
        if result.get('success', True):
            self._show_response_header()
            self._show_answer(result)
            self._show_tool_results(result)
            if show_sources:
                self._show_sources(result)
            self._show_search_info(result)
        else:
            self.show_error(f"Error: {result.get('error', 'Unknown error occurred')}")

    def _show_response_header(self):
        """Show response header"""
        console.print()
        console.print(Panel.fit("[bold cyan]BeagleMind Response[/bold cyan]", border_style="cyan"))

    def _show_answer(self, result: Dict[str, Any]):
        """Show the main answer"""
        from .utils import clean_llm_response_text

        answer = result.get('answer', 'No response generated')
        answer = clean_llm_response_text(answer)
        if answer:
            console.print(Markdown(answer))

    def _show_tool_results(self, result: Dict[str, Any]):
        """Show tool execution results"""
        tool_results = result.get('tool_results', [])
        if not tool_results:
            return

        console.print()
        tool_table = Table(title="Tools Used", show_header=True, header_style="bold magenta")
        tool_table.add_column("Tool", style="cyan")
        tool_table.add_column("Status", justify="center")
        tool_table.add_column("Result", style="dim")

        for tool_result in tool_results:
            if tool_result['result'].get('success', True):
                status = Text("Success", style="green")
            else:
                status = Text("Failed", style="red")
            result_preview = str(tool_result['result'])[:50] + "..."
            tool_table.add_row(
                tool_result['tool'],
                status,
                result_preview
            )
        console.print(tool_table)

    def _show_sources(self, result: Dict[str, Any]):
        """Show source information"""
        sources = result.get('sources', [])
        if not sources:
            return

        console.print()
        source_table = Table(title="Sources", show_header=True, header_style="bold blue")
        source_table.add_column("File", style="cyan")
        source_table.add_column("Type", style="magenta")
        source_table.add_column("Score", style="yellow")
        source_table.add_column("Preview", style="dim")

        for source in sources[:3]:  # Show top 3 sources
            preview = source.get('content', '')[:100] + "..." if len(source.get('content', '')) > 100 else source.get('content', '')
            score = source.get('composite_score', source.get('scores', {}).get('composite', 0))
            source_table.add_row(
                source.get('file_name', 'Unknown'),
                source.get('file_type', 'unknown'),
                f"{score:.3f}" if isinstance(score, (int, float)) else str(score),
                preview
            )
        console.print(source_table)

    def _show_search_info(self, result: Dict[str, Any]):
        """Show search information"""
        search_info = result.get('search_info', {})
        console.print(f"\n[dim]Search: {search_info.get('total_found', 0)} docs | "
                     f"Backend: {search_info.get('backend_used', 'Unknown').upper()} | "
                     f"Iterations: {result.get('iterations_used', 1)}[/dim]")

    def show_banner(self):
        """Show BeagleMind banner"""
        banner = """
██████╗ ███████╗ █████╗  ██████╗ ██╗     ███████╗███╗   ███╗██╗███╗   ██╗██████╗
██╔══██╗██╔════╝██╔══██╗██╔════╝ ██║     ██╔════╝████╗ ████║██║████╗  ██║██╔══██╗
██████╔╝█████╗  ███████║██║  ███╗██║     █████╗  ██╔████╔██║██║██╔██╗ ██║██║  ██║
██╔══██╗██╔══╝  ██╔══██║██║   ██║██║     ██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║██║  ██║
██████╔╝███████╗██║  ██║╚██████╔╝███████╗███████╗██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝
"""
        console.print(f"[bold cyan]{banner}[/bold cyan]")

    def show_doctor_results(self, results: Dict[str, Any]):
        """Display diagnostic results with colors and icons"""
        console.print()
        console.print(Panel.fit(
            "[bold cyan]BeagleMind Doctor[/bold cyan] - System Diagnostics",
            border_style="cyan",
            padding=(0, 2)
        ))
        console.print()

        # Helper to get status icon and color
        def get_status_display(status: str) -> tuple:
            displays = {
                "success": ("[green]●[/green]", "green"),
                "warning": ("[yellow]●[/yellow]", "yellow"),
                "error": ("[red]●[/red]", "red"),
                "info": ("[blue]●[/blue]", "blue")
            }
            return displays.get(status, ("[dim]●[/dim]", "dim"))

        # Config check
        config = results["config"]
        icon, color = get_status_display(config['status'])
        console.print(f"{icon} [bold]Configuration[/bold]")
        console.print(f"  └─ {config['message']}")
        if config.get("detail"):
            console.print(f"     [dim]{config['detail']}[/dim]")
        console.print()

        # API Keys check - using a cleaner format
        api_keys = results["api_keys"]
        icon, color = get_status_display(api_keys['status'])
        console.print(f"{icon} [bold]API Keys[/bold]")
        
        for key, info in api_keys.get("keys", {}).items():
            if info["set"]:
                status_display = "[green]Set ✓[/green]"
            else:
                status_display = "[dim]Not set[/dim]"
            optional_tag = " [dim](optional)[/dim]" if info.get("optional") else ""
            console.print(f"  ├─ {key}: {status_display}{optional_tag}")
        
        if api_keys.get("detail"):
            console.print(f"  └─ [yellow]{api_keys['detail']}[/yellow]")
        console.print()

        # RAG Backend check
        rag = results["rag_backend"]
        icon, color = get_status_display(rag['status'])
        console.print(f"{icon} [bold]RAG Backend[/bold]")
        console.print(f"  └─ {rag['message']}")
        if rag.get("detail"):
            console.print(f"     {rag['detail']}")
        if rag.get("url"):
            console.print(f"     [dim]{rag['url']}[/dim]")
        console.print()

        # Ollama check
        ollama = results["ollama"]
        icon, color = get_status_display(ollama['status'])
        console.print(f"{icon} [bold]Ollama[/bold]")
        console.print(f"  └─ {ollama['message']}")
        if ollama.get("detail"):
            console.print(f"     {ollama['detail']}")
        if ollama.get("models"):
            models_str = ", ".join(ollama['models'])
            console.print(f"     [cyan]{models_str}[/cyan]")
        console.print()

        # Overall status with better visual separation
        console.print("─" * 80)
        overall = results["overall_status"]
        if overall == "success":
            console.print("[bold green]✓[/bold green] All systems operational!")
        elif overall == "warning":
            console.print("[bold yellow]![/bold yellow] Some issues detected, but BeagleMind should work")
        else:
            console.print("[bold red]✗[/bold red] Critical issues detected, please fix before using BeagleMind")
        console.print()