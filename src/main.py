#!/usr/bin/env python3
"""
Golf Buddy CLI - A command-line interface for golf tee time analysis and web content conversion.

This module provides a CLI interface for:
1. Analyzing tee times using AI
2. Converting web pages to markdown format

Usage:
    python main.py analyze-tee-times "https://example1.com" "https://example2.com"
    python main.py convert-to-markdown "https://example.com" -o output.md
"""

from __future__ import annotations

# Python standard library imports
import logging
from typing import Optional, List
import os
import sys

# Add the src directory to the Python path when running directly
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Third-party package imports
import click
from dotenv import load_dotenv

# Local application imports
from src.html_to_md import html_to_markdown
from src.tee_time_analyzer import fetch_and_extract_tee_times
from src.web_processor import get_visible_rendered_html

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
def cli() -> None:
    """Golf Buddy - Your AI-powered tee time finder.
    
    This CLI tool helps golfers find and analyze tee times using AI,
    and provides utilities for converting web content to markdown format.
    """
    pass

@cli.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--follow/--no-follow', default=True, help='Automatically follow booking links')
def analyze_tee_times(urls: List[str], follow: bool) -> None:
    """Use AI to analyze and extract tee time information from golf course websites.
    
    Args:
        urls: One or more URLs of golf course websites to analyze
        follow: Whether to automatically follow booking links
        
    This command will:
    1. Fetch the webpage content for each URL
    2. Use AI to analyze the content
    3. Extract and display available tee times
    """
    for url in urls:
        click.echo(f"\nAnalyzing tee times from {url} using AI...")
        try:
            fetch_and_extract_tee_times(url, follow)
        except Exception as e:
            logger.error(f"Error analyzing {url}: {str(e)}")
            click.echo(f"Failed to analyze {url}: {str(e)}", err=True)

@cli.command()
@click.argument('url')
@click.option('--output', '-o', type=click.Path(), help='Output file path for the markdown content')
def convert_to_markdown(url: str, output: Optional[str]) -> None:
    """Convert a webpage to clean markdown format.
    
    Args:
        url: The URL of the webpage to convert
        output: Optional path to save the markdown content
        
    This command will:
    1. Fetch the webpage content
    2. Convert HTML to clean markdown
    3. Either save to file or print to console
    """
    try:
        logger.info(f"Fetching content from: {url}")
        markdown_content = get_visible_rendered_html(url)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            logger.info(f"Markdown content saved to: {output}")
        else:
            click.echo(markdown_content)
            
    except Exception as e:
        logger.error(f"Error converting webpage to markdown: {str(e)}")
        raise click.ClickException(str(e))

def main() -> None:
    """Main entry point for the CLI application."""
    cli()

if __name__ == '__main__':
    main() 