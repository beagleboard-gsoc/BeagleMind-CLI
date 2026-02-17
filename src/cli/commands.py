"""
CLI command definitions for BeagleMind.
"""

import click
from typing import List

from .core import BeagleMindCLI
from ..config import ConfigManager
from .display import DisplayManager


def get_available_backends() -> List[str]:
    """Get available LLM backends"""
    config_manager = ConfigManager()
    return config_manager.get_backends()


@click.group()
@click.version_option(version="1.0.0", prog_name="BeagleMind CLI")
def cli():
    """
    BeagleMind CLI - Intelligent documentation assistant for Beagleboard projects.
    
    The BeagleBoard is a low-power open-source hardware single-board computer produced by Texas Instruments.
    BeagleMind is an AI assistant designed to help developers use BeagleBoard.
    
    To ingest data, you must place files in the repository_content folder.
    """
    pass


@cli.command("list-models")
@click.option('--backend', '-b', type=click.Choice(get_available_backends(), case_sensitive=False),
              help='Show models for specific backend only')
def list_models(backend):
    """List available AI models for BeagleMind"""
    beaglemind = BeagleMindCLI()
    beaglemind.list_models(backend)


@cli.command()
@click.option('--prompt', '-p',
              help='Your question or prompt for BeagleMind (if not provided, starts interactive mode)')
@click.option('--backend', '-b', type=click.Choice(get_available_backends(), case_sensitive=False),
              help='LLM backend to use')
@click.option('--model', '-m', help='Specific model to use')
@click.option('--temperature', '-t', type=float,
              help='Temperature for response generation (0.0-1.0)')
@click.option('--strategy', '-s',
              type=click.Choice(['adaptive', 'multi_query', 'context_aware', 'default']),
              default='adaptive', help='Search strategy to use')
@click.option('--sources', is_flag=True,
              help='Show source information with the response')
@click.option('--tools/--no-tools', default=True,
              help='Enable or disable tool usage (default: enabled)')
@click.option('--interactive', '-i', is_flag=True,
              help='Force interactive chat session')
@click.option('--collection', '-c', help='Override the collection name for retrieval (default from config)')
def chat(prompt, backend, model, temperature, strategy, sources, tools, interactive, collection):
    """Chat with BeagleMind - Interactive mode by default, or single prompt with -p"""
    beaglemind = BeagleMindCLI()

    if collection:
        # Apply collection override before creating QA system
        beaglemind.config_manager.set("collection_name", collection)
        beaglemind.qa_system = None

    # Convert tools flag to use_tools boolean
    use_tools = bool(tools)

    # Start interactive mode by default when no prompt is provided
    if not prompt:
        display = DisplayManager()
        display.show_warning("Starting interactive chat mode. Use -p 'your question' for single prompt mode.\n")

        beaglemind.interactive_chat(
            backend=backend,
            model=model,
            temperature=temperature,
            search_strategy=strategy,
            show_sources=sources,
            use_tools=use_tools,
            collection=collection
        )
    else:
        # Single prompt mode when --prompt is provided
        beaglemind.chat(
            prompt=prompt,
            backend=backend,
            model=model,
            temperature=temperature,
            search_strategy=strategy,
            show_sources=sources,
            use_tools=use_tools
        )


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def ingest(path):
    """Ingest documentation from a directory."""
    display = DisplayManager()
    
    display.show_info(f"Ingesting documentation from: {path}")
    # TODO: Connect this to the actual ingestion logic in BeagleMindCLI


@cli.command("doctor")
def doctor():
    """Diagnose BeagleMind setup and connectivity issues"""
    beaglemind = BeagleMindCLI()
    beaglemind.doctor()
