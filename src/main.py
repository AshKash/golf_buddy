#!/usr/bin/env python3

import click
from dotenv import load_dotenv
from scraper import scrape_golf_course
from tee_time_analyzer import fetch_and_extract_tee_times

# Load environment variables
load_dotenv()

@click.group()
def cli():
    """Golf Buddy - Your command line golf companion."""
    pass

@cli.command()
def hello():
    """Say hello to Golf Buddy."""
    click.echo("Welcome to Golf Buddy! 🏌️‍♂️")

@cli.command()
@click.option('--url', prompt='Enter the golf course website URL', help='URL of the golf course website to scrape')
def check_tee_times(url):
    """Check available tee times from a golf course website (basic scraping)."""
    click.echo(f"Fetching tee times from {url}...")
    
    try:
        content = scrape_golf_course(url)
        click.echo("\nWebsite Content:")
        click.echo("=" * 50)
        click.echo(content)
        click.echo("=" * 50)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.option('--url', prompt='Enter the golf course website URL', help='URL of the golf course website to analyze')
@click.option('--follow/--no-follow', default=True, help='Automatically follow booking links')
def analyze_tee_times(url, follow):
    """Use AI to analyze and extract tee time information from a golf course website."""
    click.echo(f"Analyzing tee times from {url} using AI...")
    fetch_and_extract_tee_times(url, follow)

if __name__ == '__main__':
    cli() 