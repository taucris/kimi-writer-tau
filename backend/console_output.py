"""
Console-based output handler using Rich library.

This module provides a terminal-based output handler for the Kimi Novel Writing System,
displaying real-time progress, streaming content, and interactive approvals.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from backend.output_handler import OutputHandler

try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False


class ConsoleOutputHandler(OutputHandler):
    """
    Console-based output handler using Rich library.

    Displays generation progress and content in a beautiful terminal interface.
    """

    def __init__(self):
        """Initialize the console output handler."""
        self.console = Console()
        self.current_phase = None

    async def send_phase_change(self, project_id: str, from_phase: str, to_phase: str):
        """Notify of phase transition."""
        self.current_phase = to_phase
        self.console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        self.console.print(f"[bold cyan]Phase Transition: {from_phase} → {to_phase}[/bold cyan]")
        self.console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

    async def send_stream_chunk(self, project_id: str, content: str, is_reasoning: bool = False):
        """Send streaming content chunk."""
        if is_reasoning:
            # Reasoning content in dim italic
            self.console.print(f"[dim italic]{content}[/dim italic]", end="")
        else:
            # Regular content
            self.console.print(content, end="")

    async def send_tool_call(self, project_id: str, tool_name: str, arguments: Dict[str, Any]):
        """Notify of tool execution."""
        self.console.print(f"\n\n[yellow]🔧 Tool Call:[/yellow] [bold]{tool_name}[/bold]")

        # Show arguments (truncate if too long)
        if arguments:
            args_str = str(arguments)
            if len(args_str) > 200:
                args_str = args_str[:200] + "..."
            self.console.print(f"   [dim]{args_str}[/dim]")

    async def send_tool_result(self, project_id: str, tool_name: str, result: Dict[str, Any]):
        """Send tool execution result."""
        success = result.get("success", False)
        message = result.get("message", "")

        if success:
            self.console.print(f"[green]   ✓[/green] {message}")
        else:
            self.console.print(f"[red]   ✗[/red] {message}")

    async def send_token_update(self, project_id: str, token_count: int, token_limit: int):
        """Send token usage update."""
        percentage = (token_count / token_limit * 100) if token_limit > 0 else 0

        # Visual indicator for token usage
        if percentage > 90:
            color = "red"
            warning = " [WARNING: Near limit!]"
        elif percentage > 75:
            color = "yellow"
            warning = ""
        else:
            color = "green"
            warning = ""

        self.console.print(
            f"\n[{color}]📊 Tokens: {token_count:,}/{token_limit:,} "
            f"({percentage:.1f}%){warning}[/{color}]"
        )

    async def request_approval(self, project_id: str, approval_type: str, data: Dict[str, Any]):
        """Request user approval for checkpoint (async notification only)."""
        # This just notifies that approval is pending
        # Actual interactive approval happens in handle_approval_interactive
        self.console.print(f"\n[bold yellow]⏸  Approval Required:[/bold yellow] {approval_type}\n")

    async def send_progress(
        self,
        project_id: str,
        percentage: float,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Send progress update."""
        self.console.print(f"\n[cyan]📈 Progress ({percentage:.1f}%):[/cyan] {message}")

        if details:
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Key", style="dim")
            table.add_column("Value", style="white")

            for key, value in details.items():
                formatted_key = key.replace("_", " ").title()
                table.add_row(f"  {formatted_key}:", str(value))

            self.console.print(table)

    async def send_error(
        self,
        project_id: str,
        error_message: str,
        error_type: Optional[str] = None
    ):
        """Send error notification."""
        self.console.print(f"\n[bold red]❌ Error:[/bold red] {error_message}")
        if error_type:
            self.console.print(f"[dim]Type: {error_type}[/dim]")

    async def send_completion(self, project_id: str, stats: Dict[str, Any]):
        """Send novel completion notification."""
        self.console.print("\n" + "="*60)
        self.console.print("[bold green]🎉 Novel Generation Complete![/bold green]")
        self.console.print("="*60 + "\n")

        # Display statistics
        table = Table(title="Generation Statistics", show_header=True, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in stats.items():
            # Format key nicely
            formatted_key = key.replace("_", " ").title()
            table.add_row(formatted_key, str(value))

        self.console.print(table)
        self.console.print(f"\n[bold]📁 Output Directory:[/bold] output/{project_id}/\n")

    async def handle_approval_interactive(
        self,
        project_id: str,
        approval_type: str,
        data: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Handle approval interactively in terminal.

        Args:
            project_id: Project ID
            approval_type: Type of approval needed
            data: Additional data for approval

        Returns:
            Tuple of (approved: bool, notes: Optional[str])
        """
        if not QUESTIONARY_AVAILABLE:
            self.console.print(
                "[yellow]Warning: questionary not installed. Auto-approving.[/yellow]"
            )
            return True, None

        self.console.print("\n" + "="*60)
        self.console.print(f"[bold yellow]⏸  Approval Required: {approval_type.upper()}[/bold yellow]")
        self.console.print("="*60 + "\n")

        # Display relevant content based on approval type
        if approval_type == "plan":
            await self._display_plan_for_approval(project_id)
        elif approval_type.startswith("chunk"):
            chunk_num = data.get("chunk_number")
            if chunk_num:
                await self._display_chunk_for_approval(project_id, chunk_num)

        # Ask for approval
        approved = await questionary.confirm(
            "Do you approve?",
            default=True
        ).ask_async()

        notes = None
        if not approved:
            notes = await questionary.text(
                "Please provide feedback for revision:",
                multiline=True
            ).ask_async()

        return approved, notes

    async def _display_plan_for_approval(self, project_id: str):
        """Display planning materials for review."""
        from backend.tools.project import get_active_project_folder

        project_folder = get_active_project_folder()
        if not project_folder:
            return

        files = [
            ("summary.txt", "Story Summary"),
            ("dramatis_personae.txt", "Character Profiles"),
            ("story_structure.txt", "Story Structure"),
            ("plot_outline.txt", "Plot Outline")
        ]

        for filename, title in files:
            filepath = os.path.join(project_folder, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    self.console.print(f"\n[bold cyan]━━━ {title} ━━━[/bold cyan]")
                    self.console.print(Panel(content, expand=False, border_style="cyan"))
                except Exception as e:
                    self.console.print(f"[dim]Error reading {filename}: {e}[/dim]")

    async def _display_chunk_for_approval(self, project_id: str, chunk_num: int):
        """Display chunk/chapter for review."""
        from backend.tools.project import get_active_project_folder

        project_folder = get_active_project_folder()
        if not project_folder:
            return

        filepath = os.path.join(project_folder, f"chunk_{chunk_num}.txt")

        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.console.print(f"\n[bold cyan]━━━ Chunk {chunk_num} ━━━[/bold cyan]")

                # Show preview (first 1000 chars) and offer to view full
                if len(content) > 1000:
                    preview = content[:1000] + "\n\n[... content truncated ...]"
                    self.console.print(Panel(preview, expand=False, border_style="cyan"))

                    if QUESTIONARY_AVAILABLE:
                        view_full = await questionary.confirm(
                            "View full chunk?",
                            default=False
                        ).ask_async()

                        if view_full:
                            self.console.print(Panel(content, expand=False, border_style="cyan"))
                else:
                    self.console.print(Panel(content, expand=False, border_style="cyan"))

            except Exception as e:
                self.console.print(f"[dim]Error reading chunk: {e}[/dim]")
