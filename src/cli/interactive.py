"""
Interactive chat functionality for BeagleMind CLI.
"""

import os
from typing import Dict, Any

from rich.console import Console
from rich.panel import Panel

from .display import DisplayManager

# Module-level console for fallback
_console = Console()


class InteractiveChat:
    """Handles interactive chat sessions"""

    def __init__(self, qa_system, display: DisplayManager, params: Dict[str, Any]):
        self.qa_system = qa_system
        self.display = display
        self.params = params
        self.conversation_count = 0
        self.show_sources = False
        self.use_tools = False
        self._console = _console

    def start(self, search_strategy: str = "adaptive", show_sources: bool = False, use_tools: bool = False):
        """Start the interactive chat session"""
        self.show_sources = show_sources
        self.use_tools = use_tools

        self._show_welcome()
        self._chat_loop(search_strategy)

    def _show_welcome(self):
        """Show welcome message and session info"""
        self.display.show_banner()

        self._console.print("[bold]Interactive Chat Mode[/bold]")
        self._console.print(f"[dim]Backend: {self.params['backend'].upper()} | Model: {self.params['model']} | Temperature: {self.params['temperature']}[/dim]\n")

        session_panel = self._create_session_panel()
        self._console.print(session_panel)

    def _create_session_panel(self):
        """Create the session information panel"""
        return Panel(
            f"[bold]BeagleMind Interactive Chat[/bold]\n\n"
            f"[green]Commands:[/green]\n"
            f"• Type your questions naturally\n"
            f"• [cyan]/help[/cyan] - Show available commands\n"
            f"• [cyan]/sources[/cyan] - Toggle source display ({self.show_sources})\n"
            f"• [cyan]/tools[/cyan] - Toggle tool usage ({'enabled' if self.use_tools else 'disabled'})\n"
            f"• [cyan]/config[/cyan] - Show current configuration\n"
            f"• [cyan]/clear[/cyan] - Clear screen\n"
            f"• [cyan]/exit[/cyan] or [cyan]/quit[/cyan] - Exit chat\n"
            f"• [cyan]Ctrl+C[/cyan] - Emergency exit\n\n"
            f"[yellow]Tip:[/yellow] BeagleMind can create files, run commands, and analyze code!",
            title="🚀 Welcome to BeagleMind",
            border_style="green"
        )

    def _chat_loop(self, search_strategy: str):
        """Main chat loop"""
        try:
            while True:
                try:
                    user_input = self._get_user_input()
                    if not user_input:
                        continue

                    if self._handle_special_commands(user_input):
                        continue

                    self._process_chat_input(user_input, search_strategy)
                    self._show_separator()

                except KeyboardInterrupt:
                    self._console.print("\n[yellow]Use /exit or /quit to end the session gracefully.[/yellow]")
                    continue
                except EOFError:
                    self._console.print("\n[yellow]👋 Session ended. Goodbye![/yellow]")
                    break

        except Exception as e:
            self._console.print(f"\n[red]Unexpected error in interactive mode: {e}[/red]")

    def _get_user_input(self):
        """Get user input with prompt"""
        prompt_text = f"[bold cyan]BeagleMind[/bold cyan] [dim]({self.conversation_count + 1})[/dim] > "
        self._console.print(prompt_text, end="")
        return input().strip()

    def _handle_special_commands(self, user_input: str) -> bool:
        """Handle special commands, return True if handled"""
        command = user_input.lower()

        if command in ['/exit', '/quit', 'exit', 'quit']:
            self._show_goodbye()
            exit(0)
        elif command == '/help':
            self._show_help()
            return True
        elif command == '/sources':
            self._toggle_sources()
            return True
        elif command == '/tools':
            self._toggle_tools()
            return True
        elif command == '/config':
            self._show_config()
            return True
        elif command == '/clear':
            self._clear_screen()
            return True

        return False

    def _process_chat_input(self, user_input: str, search_strategy: str):
        """Process regular chat input"""
        self.conversation_count += 1

        self._console.print(f"\n[dim]🧠 BeagleMind is thinking...[/dim]")

        try:
            result = self.qa_system.ask_question(
                question=user_input,
                search_strategy=search_strategy,
                model_name=self.params["model"],
                temperature=self.params["temperature"],
                llm_backend=self.params["backend"],
                use_tools=self.use_tools
            )

            self.display.show_chat_response(result, self.show_sources)

        except Exception as e:
            self.display.show_error(f"Failed to process question: {e}")

    def _show_goodbye(self):
        """Show goodbye message"""
        self._console.print("[yellow]👋 Goodbye! Thanks for using BeagleMind![/yellow]")

    def _show_help(self):
        """Show help information"""
        help_panel = Panel(
            f"[bold]BeagleMind Interactive Chat Commands[/bold]\n\n"
            f"[green]Chat Commands:[/green]\n"
            f"• [cyan]/help[/cyan] - Show this help message\n"
            f"• [cyan]/sources[/cyan] - Toggle source information display\n"
            f"• [cyan]/tools[/cyan] - Toggle tool usage (file operations, commands, etc.)\n"
            f"• [cyan]/config[/cyan] - Show current session configuration\n"
            f"• [cyan]/clear[/cyan] - Clear the screen\n"
            f"• [cyan]/exit[/cyan] or [cyan]/quit[/cyan] - End the session\n\n"
            f"[green]Example Questions:[/green]\n"
            f"• 'Create a Python script for LED blinking on BeagleY-AI'\n"
            f"• 'How do I setup GPIO on BeagleBoard?'\n"
            f"• 'Generate a systemd service file for my app'\n"
            f"• 'What are the pin configurations for BeagleY-AI?'\n"
            f"• 'List files in the current directory'\n"
            f"• 'Analyze the code in main.py'\n\n"
            f"[yellow]Tips:[/yellow]\n"
            f"• BeagleMind can create and edit files automatically (when tools are enabled)\n"
            f"• Ask for specific BeagleBoard/BeagleY-AI configurations\n"
            f"• Request code analysis and improvements\n"
            f"• Use natural language - no special syntax needed\n"
            f"• Disable tools with [cyan]/tools[/cyan] for text-only responses",
            title="📚 Help",
            border_style="blue"
        )
        self._console.print(help_panel)

    def _toggle_sources(self):
        """Toggle source display"""
        self.show_sources = not self.show_sources
        self.display.show_success(f"✓ Source display: {'enabled' if self.show_sources else 'disabled'}")

    def _toggle_tools(self):
        """Toggle tool usage"""
        self.use_tools = not self.use_tools
        self.display.show_success(f"✓ Tool usage: {'enabled' if self.use_tools else 'disabled'}")

    def _show_config(self):
        """Show current configuration"""
        config_panel = Panel(
            f"[bold]Current Session Configuration[/bold]\n\n"
            f"[cyan]LLM Backend:[/cyan] {self.params['backend'].upper()}\n"
            f"[cyan]Model:[/cyan] {self.params['model']}\n"
            f"[cyan]Temperature:[/cyan] {self.params['temperature']}\n"
            f"[cyan]Show Sources:[/cyan] {'Yes' if self.show_sources else 'No'}\n\n"
            f"[dim]Collection:[/dim] beagleboard",
            title="Configuration",
            border_style="magenta"
        )
        self._console.print(config_panel)

    def _clear_screen(self):
        """Clear the screen and reset conversation"""
        os.system('clear' if os.name == 'posix' else 'cls')
        self.display.show_banner()

        self._console.print("[bold]Interactive Chat Mode - Session Cleared[/bold]\n")

        try:
            self.qa_system.reset_conversation()
        except Exception:
            pass

    def _show_separator(self):
        """Show conversation separator"""
        self._console.print("\n" + "─" * 60 + "\n")