#!/usr/bin/env python3
"""
Tee Time Analyzer - AI-powered analysis of golf course tee times.
"""

import logging
from typing import Optional, List, Dict, Any
import json
from openai import OpenAI
from dotenv import load_dotenv
import click
from src.web_processor import get_visible_rendered_html, close_processor

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI()

def fetch_and_extract_tee_times(url: str, follow: bool = True) -> None:
    """
    Fetch and analyze tee times from a golf course website.
    
    Args:
        url: The URL of the golf course website
        follow: Whether to follow booking links
    """
    try:
        # Get the initial page content
        content = get_visible_rendered_html(url)
        if not content:
            raise click.ClickException("Failed to fetch page content")
            
        # Analyze the content with GPT-4
        analysis = analyze_tee_times(content)
        
        #BUG this needs to be analysed and fixed
        # Loop here if follow is true and the analysis dict doesnt any of the booking links
        booking_links = analysis.get("booking_links", None)
        url = None
        if follow:
            for booking_link in booking_links:
                url = booking_link.get("url", None)
                logger.info(f"Fetching {url}...")
                content = get_visible_rendered_html(url)
                analysis = analyze_tee_times(content)
                booking_links = analysis.get("booking_links", None)
                url = None
                
        # Display the results
        display_results(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing tee times: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        # Clean up
        close_processor()

def analyze_tee_times(content: str) -> Dict[str, Any]:
    """
    Use GPT-4 to analyze tee time information from the content.
    
    Args:
        content: The markdown content to analyze
        
    Returns:
        Dict containing the analysis results
    """
    try:
        # Prepare the prompt
        prompt = f"""
        Analyze this golf course website content and extract tee time information for a maximum of 5 slots.
        
        Content:
        {content}
        
        Extract and return a JSON object with the following structure:
        {{
            "next_available_time": "YYYY-MM-DD HH:MM" or null,
            "available_times": [
                {{
                    "time": "YYYY-MM-DD HH:MM",
                    "players": number,
                    "price": "string",
                    "notes": "string"
                }}
            ],
            "booking_links": [
                {{
                    "text": "string",
                    "url": "string"
                }}
            ],
            "summary": "string"
        }}
        
        IMPORTANT: Your response must be a valid JSON object. Do not include any other text.
        """
        
        # Call GPT-4
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a golf tee time analysis expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        # Get the response content
        result = response.choices[0].message.content
        logger.info(f"Raw GPT response: {result}")
        
        try:
            # Parse the response
            analysis = json.loads(result)
            
            # Validate the response structure
            required_keys = ["next_available_time", "available_times", "booking_links", "summary"]
            missing_keys = [key for key in required_keys if key not in analysis]
            if missing_keys:
                raise ValueError(f"Missing required keys in response: {missing_keys}")
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from GPT: {result}")
            raise ValueError(f"Invalid JSON response from GPT: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error in GPT analysis: {str(e)}")
        raise

def display_results(analysis: Dict[str, Any]) -> None:
    """
    Display the analysis results in a user-friendly format.
    
    Args:
        analysis: The analysis results dictionary
    """
    # Display next available time
    if analysis.get("next_available_time"):
        click.echo(f"\nNext available tee time: {analysis['next_available_time']}")
    else:
        click.echo("\nNo available tee times found")
    
    # Display all available times
    if analysis.get("available_times"):
        click.echo("\nAvailable tee times:")
        for time in analysis["available_times"]:
            click.echo(f"- {time['time']}: {time['players']} players, {time['price']}")
            if time.get("notes"):
                click.echo(f"  Note: {time['notes']}")
    
    # Display booking links
    if analysis.get("booking_links"):
        click.echo("\nBooking links:")
        for link in analysis["booking_links"]:
            click.echo(f"- {link['text']}: {link['url']}")
    
    # Display summary
    if analysis.get("summary"):
        click.echo(f"\nSummary: {analysis['summary']}")

@click.command()
@click.option('--url', prompt='Enter the golf course website URL', help='URL of the golf course website to analyze')
@click.option('--follow/--no-follow', default=True, help='Automatically follow booking links')
def main(url, follow):
    """Main function to test the tee time extraction."""
    fetch_and_extract_tee_times(url, follow)

if __name__ == "__main__":
    main() 