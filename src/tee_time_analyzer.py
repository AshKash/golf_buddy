import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import httpx
from dotenv import load_dotenv
import click
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from web_processor import get_visible_rendered_html

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OPENAI_MODEL = "gpt-4"
OPENAI_TEMPERATURE = 0.2
MAX_HTML_LENGTH = 40000
MAX_SAMPLE_LENGTH = 5000
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5

# Load environment variables
load_dotenv()

# Get and validate API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    click.echo(click.style("Error: OPENAI_API_KEY not found in .env file", fg='red'))
    click.echo(click.style("Please create a .env file with your OpenAI API key:", fg='yellow'))
    click.echo(click.style("OPENAI_API_KEY=your_api_key_here", fg='yellow'))
    exit(1)

# Debug: Show masked API key
masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'

# Initialize OpenAI client using httpx (recommended)
client = OpenAI(api_key=api_key, http_client=httpx.Client())

def is_valid_url(url):
    """Check if the URL is valid and absolute."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except Exception as e:
        logger.error(f"URL validation error: {str(e)}")
        return False

def make_absolute_url(base_url, link):
    """Convert relative URL to absolute URL."""
    try:
        if is_valid_url(link):
            return link
        return urljoin(base_url, link)
    except Exception as e:
        logger.error(f"URL conversion error: {str(e)}")
        return None

def fetch_and_extract_tee_times(url: str, follow_link: bool = True):
    """
    This function goes to a website (URL), reads it, and tries to find the next available tee time.
    If it doesn't find it, it suggests the most likely link to book tee times.
    """
    try:
        # Validate URL first
        if not is_valid_url(url):
            click.echo(click.style("Invalid URL format. Please provide a valid URL starting with http:// or https://", fg='red'))
            return

        # Get rendered HTML using Playwright
        logger.info(f"Fetching rendered HTML from {url}")
        rendered_html = get_visible_rendered_html(url)
        
        if not rendered_html:
            click.echo(click.style("No content could be extracted from the page.", fg='red'))
            return

        # Debug: Show content lengths and sample
        click.echo(click.style(f"Rendered HTML length: {len(rendered_html)} characters", fg='blue'))
        click.echo(click.style("\nSample of rendered HTML:", fg='blue'))
        click.echo(click.style(rendered_html[:MAX_SAMPLE_LENGTH] + "...", fg='blue'))

        # Step 3: Prepare the prompt for GPT-4
        current_time = datetime.now().strftime("%I:%M %p")
        prompt = f"""
You are helping a golfer find the next available tee time on a golf course website. You will be given cleaned Markdown content to parse.

Current time: {current_time}

Below is the cleaned Markdown content of a golf-related website page:
{rendered_html[:MAX_HTML_LENGTH]}

Your task:
1. Parse the Markdown and look for the next available tee time on this page. If you find it, format it as:
   NEXT TEE TIME:
   - Time: [exact time]
   - Available for: [number of players]
   - Price: [if available]
   - Notes: [any important information]

2. If you don't find a tee time on this page, analyze the Markdown and find links that might lead to a tee time booking page. Look for:
   - Links containing words like "tee time", "book", "reserve", "schedule", "golf", "play"
   - Links that appear to be booking buttons or navigation items
   - Links that are visible and prominently displayed or in the main navigation
   
   Extract the most relevant booking link and format it as:
   BOOKING LINK:
   - URL: [full URL]
   - Text: [link text or button text]
   - Reason: [why this link is likely to lead to tee time booking]

Be very specific and concise. If you find a tee time, only show the next available one. If you don't find a tee time, only show the most relevant booking link with its context.
"""

        # Debug: Show that we're about to make the API call
        click.echo(click.style("\nMaking OpenAI API request...", fg='blue'))
        click.echo(click.style(f"Model: {OPENAI_MODEL}", fg='blue'))
        click.echo(click.style(f"Temperature: {OPENAI_TEMPERATURE}", fg='blue'))
        click.echo(click.style(f"Prompt length: {len(prompt)} characters", fg='blue'))

        try:
            # Step 4: Get AI analysis
            click.echo(click.style(f"Using OpenAI API Key: {masked_key}", fg='blue'))  
            click.echo(click.style("Prompt ready. Sending to OpenAI...", fg='blue'))
            completion = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=OPENAI_TEMPERATURE
            )
            click.echo(click.style("✅ OpenAI API request successful", fg='green'))
        except Exception as api_error:
            click.echo(click.style(f"❌ OpenAI API request failed: {str(api_error)}", fg='red'))
            return

        # Step 5: Display results
        answer = completion.choices[0].message.content.strip()
        
        # Only show the relevant information
        if "NEXT TEE TIME:" in answer:
            # Extract only the tee time information
            tee_time_info = answer.split("NEXT TEE TIME:")[1].strip()
            click.echo("\n" + click.style("🔍 Next Available Tee Time:", fg='green', bold=True))
            # Format each line with a different color
            for line in tee_time_info.split('\n'):
                if line.strip():
                    if 'Time:' in line:
                        click.echo(click.style(line.strip(), fg='yellow'))
                    elif 'Available for:' in line:
                        click.echo(click.style(line.strip(), fg='cyan'))
                    elif 'Price:' in line:
                        click.echo(click.style(line.strip(), fg='magenta'))
                    elif 'Notes:' in line:
                        click.echo(click.style(line.strip(), fg='blue'))
                    else:
                        click.echo(line.strip())
        else:
            # Extract only the booking link information
            booking_info = answer.split("BOOKING LINK:")[1].strip() if "BOOKING LINK:" in answer else answer
            click.echo("\n" + click.style("🔍 Booking Link:", fg='green', bold=True))
            for line in booking_info.split('\n'):
                if line.strip():
                    if 'URL:' in line:
                        click.echo(click.style(line.strip(), fg='yellow'))
                    elif 'Text:' in line:
                        click.echo(click.style(line.strip(), fg='cyan'))
                    elif 'Reason:' in line:
                        click.echo(click.style(line.strip(), fg='blue'))
                    else:
                        click.echo(line.strip())
            
            # Ask if user wants to follow the link
            if follow_link and "URL:" in booking_info and click.confirm("\nWould you like to check this booking link?"):
                booking_url = next((line.split("URL:")[1].strip() for line in booking_info.split('\n') if "URL:" in line), None)
                if booking_url:
                    click.echo("\n" + click.style("🔄 Following booking link...", fg='green'))
                    fetch_and_extract_tee_times(booking_url, follow_link=False)

    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))

@click.command()
@click.option('--url', prompt='Enter the golf course website URL', help='URL of the golf course website to analyze')
@click.option('--follow/--no-follow', default=True, help='Automatically follow booking links')
def main(url, follow):
    """Main function to test the tee time extraction."""
    fetch_and_extract_tee_times(url, follow)

if __name__ == "__main__":
    main() 