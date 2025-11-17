"""
Interactive terminal-based UI for the Kimi Novel Writing System.

This module provides a guided Q&A experience for novel generation,
replacing the web-based interface with a rich terminal experience.
"""

import asyncio
import os
import sys
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv

# Check for required packages
try:
    import questionary
    from questionary import Choice
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False
    print("Warning: questionary not installed. Install with: pip install questionary")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich not installed. Install with: pip install rich")

from backend.config import (
    NovelConfig, NovelLength, get_default_config,
    generate_project_id, sanitize_project_name,
    WritingSampleConfig, CheckpointConfig, AgentConfig,
    save_config_to_file, get_config_path, AVAILABLE_MODELS,
    load_config_from_file
)
from backend.state_manager import (
    create_new_state, save_state, load_state,
    resume_generation, get_progress_percentage
)
from backend.agent_loop import AgentLoop
from backend.console_output import ConsoleOutputHandler
from backend.writing_samples import list_available_samples, get_writing_sample

# Load environment variables
load_dotenv()

# Initialize console
console = Console() if RICH_AVAILABLE else None


# ============================================================================
# Configuration Collection
# ============================================================================

async def collect_basic_info() -> dict:
    """Collect basic project information."""
    if not QUESTIONARY_AVAILABLE:
        print("\nError: questionary is required for interactive mode.")
        print("Install with: pip install questionary rich")
        sys.exit(1)

    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold cyan]Kimi Novel Writing System[/bold cyan]\n"
            "Interactive Novel Generation",
            border_style="cyan"
        ))
        console.print("\n[bold]Let's create your novel![/bold]\n")
    else:
        print("\n=== Kimi Novel Writing System ===")
        print("Interactive Novel Generation\n")
        print("Let's create your novel!\n")

    project_name = await questionary.text(
        "Project name:",
        validate=lambda x: len(x) > 0 or "Project name is required"
    ).ask_async()

    theme = await questionary.text(
        "What's your novel about? (theme/premise):",
        multiline=True,
        validate=lambda x: len(x) > 10 or "Please provide more detail (at least 10 characters)"
    ).ask_async()

    genre = await questionary.text(
        "Genre (optional):",
        default=""
    ).ask_async()

    return {
        "project_name": project_name,
        "theme": theme,
        "genre": genre if genre else None
    }


async def collect_novel_length() -> tuple[NovelLength, Optional[int]]:
    """Collect novel length preference."""
    if RICH_AVAILABLE:
        console.print("\n[bold]Novel Length[/bold]")
        console.print("Choose the target length for your novel:\n")
    else:
        print("\nNovel Length")
        print("Choose the target length for your novel:\n")

    choices = [
        Choice(
            title="Short Story (3,000-10,000 words, ~1-3 chunks)",
            value=NovelLength.SHORT_STORY
        ),
        Choice(
            title="Novella (20,000-50,000 words, ~5-15 chunks)",
            value=NovelLength.NOVELLA
        ),
        Choice(
            title="Novel (50,000-110,000 words, ~15-30 chunks)",
            value=NovelLength.NOVEL
        ),
        Choice(
            title="Very Long Novel (110,000-200,000 words, ~30-50 chunks)",
            value=NovelLength.VERY_LONG_NOVEL
        ),
        Choice(
            title="Custom (specify word count)",
            value=NovelLength.CUSTOM
        )
    ]

    length = await questionary.select(
        "Select length:",
        choices=choices
    ).ask_async()

    custom_word_count = None
    if length == NovelLength.CUSTOM:
        custom_word_count = await questionary.text(
            "Target word count:",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Enter a positive number"
        ).ask_async()
        custom_word_count = int(custom_word_count)

    return length, custom_word_count


async def collect_model_selection() -> str:
    """Collect AI model preference."""
    if RICH_AVAILABLE:
        console.print("\n[bold]AI Model Selection[/bold]")
        console.print("Choose which AI model to use for generation:\n")
    else:
        print("\nAI Model Selection")
        print("Choose which AI model to use for generation:\n")

    choices = []
    for model in AVAILABLE_MODELS:
        title_parts = [f"{model['name']} ({model['provider']})"]

        if model.get('pricing'):
            title_parts.append(f"- {model['pricing']}")

        if model.get('supports_reasoning'):
            title_parts.append("- Has reasoning")

        choices.append(Choice(
            title=" ".join(title_parts),
            value=model['id']
        ))

    model_id = await questionary.select(
        "Select model:",
        choices=choices
    ).ask_async()

    return model_id


async def collect_writing_sample() -> WritingSampleConfig:
    """Collect writing sample preference."""
    if RICH_AVAILABLE:
        console.print("\n[bold]Writing Style (Optional)[/bold]")
        console.print("You can provide a writing sample to guide the AI's style.\n")
    else:
        print("\nWriting Style (Optional)")
        print("You can provide a writing sample to guide the AI's style.\n")

    use_sample = await questionary.confirm(
        "Would you like to use a writing sample?",
        default=False
    ).ask_async()

    if not use_sample:
        return WritingSampleConfig(enabled=False)

    # List available preset samples
    samples = list_available_samples()

    choices = [
        Choice(title=f"{s['name']} - {s['author']}", value=s['id'])
        for s in samples
    ]
    choices.append(Choice(title="Use custom text", value="custom"))

    sample_id = await questionary.select(
        "Select writing sample:",
        choices=choices
    ).ask_async()

    custom_text = None
    if sample_id == "custom":
        if RICH_AVAILABLE:
            console.print("\n[dim]Enter your writing sample (press ESC + Enter when done):[/dim]")
        else:
            print("\nEnter your writing sample (press ESC + Enter when done):")

        custom_text = await questionary.text(
            "Writing sample:",
            multiline=True,
            validate=lambda x: len(x) >= 100 or "Sample must be at least 100 characters"
        ).ask_async()

    return WritingSampleConfig(
        enabled=True,
        sample_id=sample_id,
        custom_text=custom_text
    )


async def collect_checkpoints() -> CheckpointConfig:
    """Collect approval checkpoint preferences."""
    if RICH_AVAILABLE:
        console.print("\n[bold]Approval Checkpoints[/bold]")
        console.print(
            "You can require manual approval at key stages.\n"
            "This allows you to review and approve/reject before proceeding.\n"
        )
    else:
        print("\nApproval Checkpoints")
        print("You can require manual approval at key stages.")
        print("This allows you to review and approve/reject before proceeding.\n")

    require_plan = await questionary.confirm(
        "Require approval after planning phase?",
        default=True
    ).ask_async()

    require_chunk = await questionary.confirm(
        "Require approval after each chunk/chapter?",
        default=False
    ).ask_async()

    return CheckpointConfig(
        require_plan_approval=require_plan,
        require_chunk_approval=require_chunk
    )


async def collect_agent_settings() -> AgentConfig:
    """Collect agent behavior settings."""
    if RICH_AVAILABLE:
        console.print("\n[bold]Quality Control Settings[/bold]")
        console.print(
            "Configure how many times the AI will critique and revise its work.\n"
        )
    else:
        print("\nQuality Control Settings")
        print("Configure how many times the AI will critique and revise its work.\n")

    use_defaults = await questionary.confirm(
        "Use default settings? (2 critique iterations for plan and chunks)",
        default=True
    ).ask_async()

    if use_defaults:
        return AgentConfig()

    plan_critique_iterations = await questionary.select(
        "Max plan critique iterations:",
        choices=[str(i) for i in range(1, 11)]
    ).ask_async()

    write_critique_iterations = await questionary.select(
        "Max chunk critique iterations:",
        choices=[str(i) for i in range(1, 11)]
    ).ask_async()

    return AgentConfig(
        max_plan_critique_iterations=int(plan_critique_iterations),
        max_write_critique_iterations=int(write_critique_iterations)
    )


async def collect_configuration() -> NovelConfig:
    """Collect all configuration through interactive prompts."""
    # Basic info
    basic_info = await collect_basic_info()

    # Novel length
    length, custom_word_count = await collect_novel_length()

    # Model selection
    model_id = await collect_model_selection()

    # Writing sample
    writing_sample = await collect_writing_sample()

    # Checkpoints
    checkpoints = await collect_checkpoints()

    # Agent settings
    agent_settings = await collect_agent_settings()

    # Get API keys from environment
    moonshot_api_key = os.getenv("MOONSHOT_API_KEY")
    deepinfra_api_key = os.getenv("DEEPINFRA_API_KEY")

    # Validate API key for selected model
    model_config = None
    for model in AVAILABLE_MODELS:
        if model['id'] == model_id:
            model_config = model
            break

    if not model_config:
        if RICH_AVAILABLE:
            console.print(f"[red]Error: Unknown model {model_id}[/red]")
        else:
            print(f"Error: Unknown model {model_id}")
        sys.exit(1)

    provider = model_config['provider']
    if provider == 'moonshot' and not moonshot_api_key:
        if RICH_AVAILABLE:
            console.print("[red]Error: MOONSHOT_API_KEY not set in environment[/red]")
            console.print("Please set it in your .env file or environment variables")
        else:
            print("Error: MOONSHOT_API_KEY not set in environment")
            print("Please set it in your .env file or environment variables")
        sys.exit(1)
    elif provider == 'deepinfra' and not deepinfra_api_key:
        if RICH_AVAILABLE:
            console.print("[red]Error: DEEPINFRA_API_KEY not set in environment[/red]")
            console.print("Please set it in your .env file or environment variables")
        else:
            print("Error: DEEPINFRA_API_KEY not set in environment")
            print("Please set it in your .env file or environment variables")
        sys.exit(1)

    # Generate project ID (includes sanitized name + timestamp)
    project_id = generate_project_id(basic_info['project_name'])
    sanitized_name = sanitize_project_name(basic_info['project_name'])

    # Build config
    config = get_default_config(
        project_name=sanitized_name,
        theme=basic_info['theme'],
        moonshot_api_key=moonshot_api_key,
        deepinfra_api_key=deepinfra_api_key,
        model_id=model_id
    )

    config.project_id = project_id
    config.novel_length = length
    config.custom_word_count = custom_word_count
    config.genre = basic_info['genre']
    config.writing_sample = writing_sample
    config.checkpoints = checkpoints
    config.agent = agent_settings

    # Show summary
    await display_config_summary(config)

    # Confirm
    proceed = await questionary.confirm(
        "\nProceed with generation?",
        default=True
    ).ask_async()

    if not proceed:
        if RICH_AVAILABLE:
            console.print("[yellow]Generation cancelled.[/yellow]")
        else:
            print("Generation cancelled.")
        sys.exit(0)

    return config


async def display_config_summary(config: NovelConfig):
    """Display configuration summary for review."""
    if RICH_AVAILABLE:
        console.print("\n" + "="*60)
        console.print("[bold cyan]Configuration Summary[/bold cyan]")
        console.print("="*60 + "\n")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Project Name", config.project_name)
        table.add_row("Theme", config.theme[:100] + ("..." if len(config.theme) > 100 else ""))
        table.add_row("Genre", config.genre or "Not specified")
        table.add_row("Length", config.novel_length.value.replace("_", " ").title())

        if config.custom_word_count:
            table.add_row("Target Words", f"{config.custom_word_count:,}")

        # Find model name
        model_name = config.api.model_id
        for model in AVAILABLE_MODELS:
            if model['id'] == config.api.model_id:
                model_name = model['name']
                break

        table.add_row("AI Model", model_name)
        table.add_row("Writing Sample", "Yes" if config.writing_sample.enabled else "No")
        table.add_row("Plan Approval", "Yes" if config.checkpoints.require_plan_approval else "No")
        table.add_row("Chunk Approval", "Yes" if config.checkpoints.require_chunk_approval else "No")
        table.add_row("Plan Critique Iterations", str(config.agent.max_plan_critique_iterations))
        table.add_row("Chunk Critique Iterations", str(config.agent.max_write_critique_iterations))

        console.print(table)
    else:
        print("\n" + "="*60)
        print("Configuration Summary")
        print("="*60 + "\n")
        print(f"Project Name: {config.project_name}")
        print(f"Theme: {config.theme[:100]}...")
        print(f"Genre: {config.genre or 'Not specified'}")
        print(f"Length: {config.novel_length.value.replace('_', ' ').title()}")
        if config.custom_word_count:
            print(f"Target Words: {config.custom_word_count:,}")
        print(f"Writing Sample: {'Yes' if config.writing_sample.enabled else 'No'}")
        print(f"Plan Approval: {'Yes' if config.checkpoints.require_plan_approval else 'No'}")
        print(f"Chunk Approval: {'Yes' if config.checkpoints.require_chunk_approval else 'No'}")


# ============================================================================
# Generation Execution
# ============================================================================

async def run_generation(config: NovelConfig):
    """Run the novel generation process with console output."""
    # Create project directory structure
    project_dir = Path(f"output/{config.project_id}")
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "planning").mkdir(exist_ok=True)
    (project_dir / "manuscript").mkdir(exist_ok=True)
    (project_dir / "critiques").mkdir(exist_ok=True)
    (project_dir / "conversation_history").mkdir(exist_ok=True)

    # Save config
    save_config_to_file(config, get_config_path(config.project_id))

    # Create initial state
    state = create_new_state(config.project_id)
    state.paused = False  # Start immediately
    save_state(state)

    if RICH_AVAILABLE:
        console.print(f"\n[bold green]Starting generation...[/bold green]")
        console.print(f"[dim]Project ID: {config.project_id}[/dim]")
        console.print(f"[dim]Output: {project_dir.absolute()}[/dim]\n")
    else:
        print(f"\nStarting generation...")
        print(f"Project ID: {config.project_id}")
        print(f"Output: {project_dir.absolute()}\n")

    # Create console output handler
    output_handler = ConsoleOutputHandler()

    # Run agent loop
    loop = AgentLoop(
        project_id=config.project_id,
        config=config,
        state=state,
        output_handler=output_handler
    )

    try:
        await loop.run()
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n\n[yellow]Generation interrupted by user.[/yellow]")
            console.print(f"[dim]Progress saved. Resume with: python -m backend.cli --resume {config.project_id}[/dim]")
        else:
            print("\n\nGeneration interrupted by user.")
            print(f"Progress saved. Resume with: python -m backend.cli --resume {config.project_id}")
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"\n\n[bold red]Error during generation:[/bold red] {e}")
            console.print(f"[dim]Progress saved. Check logs for details.[/dim]")
        else:
            print(f"\n\nError during generation: {e}")
            print("Progress saved. Check logs for details.")
        raise


# ============================================================================
# Project Management
# ============================================================================

async def list_projects():
    """List all existing projects."""
    output_dir = Path("output")
    if not output_dir.exists():
        if RICH_AVAILABLE:
            console.print("[yellow]No projects found.[/yellow]")
        else:
            print("No projects found.")
        return

    projects = []
    for project_dir in output_dir.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith('.'):
            config_path = project_dir / ".novel_config.json"
            state_path = project_dir / ".novel_state.json"

            if config_path.exists() and state_path.exists():
                try:
                    config = load_config_from_file(str(config_path))
                    state = load_state(project_dir.name)

                    projects.append({
                        'id': project_dir.name,
                        'name': config.project_name,
                        'phase': state.phase.value,
                        'progress': get_progress_percentage(state),
                        'created': state.created_at
                    })
                except Exception:
                    continue

    if not projects:
        if RICH_AVAILABLE:
            console.print("[yellow]No valid projects found.[/yellow]")
        else:
            print("No valid projects found.")
        return

    # Display projects
    if RICH_AVAILABLE:
        table = Table(title="Your Novel Projects", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Phase", style="yellow")
        table.add_column("Progress", style="green")
        table.add_column("Created", style="dim")

        for proj in sorted(projects, key=lambda x: x['created'], reverse=True):
            table.add_row(
                proj['name'],
                proj['phase'],
                f"{proj['progress']:.1f}%",
                proj['created'].strftime("%Y-%m-%d %H:%M")
            )

        console.print(table)
    else:
        print("\nYour Novel Projects\n")
        print(f"{'Name':<30} {'Phase':<20} {'Progress':<10} {'Created':<20}")
        print("-" * 80)
        for proj in sorted(projects, key=lambda x: x['created'], reverse=True):
            print(f"{proj['name']:<30} {proj['phase']:<20} {proj['progress']:>6.1f}%    {proj['created'].strftime('%Y-%m-%d %H:%M')}")


async def resume_project(project_id: str):
    """Resume an existing project."""
    try:
        config = load_config_from_file(get_config_path(project_id))
        state = load_state(project_id)
    except FileNotFoundError:
        if RICH_AVAILABLE:
            console.print(f"[red]Error: Project {project_id} not found.[/red]")
        else:
            print(f"Error: Project {project_id} not found.")
        return

    if RICH_AVAILABLE:
        console.print(f"\n[bold]Resuming project:[/bold] {config.project_name}")
        console.print(f"[dim]Current phase: {state.phase.value}[/dim]")
        console.print(f"[dim]Progress: {get_progress_percentage(state):.1f}%[/dim]\n")
    else:
        print(f"\nResuming project: {config.project_name}")
        print(f"Current phase: {state.phase.value}")
        print(f"Progress: {get_progress_percentage(state):.1f}%\n")

    # Resume generation
    state = resume_generation(state)
    save_state(state)

    await run_generation(config)


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Kimi Novel Writing System - Interactive Terminal UI"
    )
    parser.add_argument(
        '--resume',
        type=str,
        metavar='PROJECT_ID',
        help='Resume an existing project by ID'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all projects'
    )

    args = parser.parse_args()

    # Handle commands
    if args.list:
        await list_projects()
        return

    if args.resume:
        await resume_project(args.resume)
        return

    # Default: Start new project
    config = await collect_configuration()
    await run_generation(config)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n[yellow]Goodbye![/yellow]")
        else:
            print("\nGoodbye!")
        sys.exit(0)
