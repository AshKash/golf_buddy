import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import httpx
from dotenv import load_dotenv
import click
from datetime import datetime
from urllib.parse import urljoin, urlparse
import nltk
from nltk.util import clean_html
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except Exception as e:
        logger.error(f"Failed to download NLTK data: {str(e)}")
        click.echo(click.style("Warning: NLTK data download failed. Some features may not work correctly.", fg='yellow'))

# Constants
OPENAI_MODEL = "gpt-4"
OPENAI_TEMPERATURE = 0.2
MAX_HTML_LENGTH = 40000
MAX_SAMPLE_LENGTH = 50000
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5

# Template-related terms to remove
TEMPLATE_TERMS = ['template', 'theme', 'framework', 'bootstrap', 'uikit']
MEDIA_PATHS = [
    '/templates/', '/themes/', '/framework/', '/vendor/', '/resources/', 
    '/assets/', '/css/', '/js/', '/images/', '/img/', '/media/', 
    '/components/', '/com_', '/mod_', '/plugins/', '/libraries/'
]
AD_TERMS = ['ad', 'analytics', 'tracking', 'cookie', 'banner', 'popup', 'modal']
STYLE_ATTRIBUTES = [
    'align', 'bgcolor', 'color', 'face', 'size', 'width', 'height', 
    'margin', 'padding', 'border', 'background', 'font', 'text-align',
    'font-family', 'font-size', 'font-weight', 'font-style', 'line-height',
    'text-decoration', 'text-transform', 'letter-spacing', 'word-spacing'
]

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

def clean_html_content(html_content: str) -> str:
    """
    Cleans HTML content by removing scripts, styles, templates, ads, tracking,
    and most presentational attributes. Returns simplified, readable HTML.
    """
    if not html_content or not isinstance(html_content, str):
        logger.warning("Invalid HTML content provided")
        return ""

    try:
        # First pass: Use NLTK's clean_html for initial cleaning
        try:
            cleaned_html = clean_html(html_content)
            if not cleaned_html:
                logger.warning("NLTK clean_html returned empty result")
                cleaned_html = html_content
        except Exception as e:
            logger.warning(f"NLTK clean_html failed: {str(e)}")
            cleaned_html = html_content
        
        # Second pass: Use BeautifulSoup for more specific cleaning
        try:
            soup = BeautifulSoup(cleaned_html, 'html.parser')
        except Exception as e:
            logger.error(f"BeautifulSoup parsing failed: {str(e)}")
            return cleaned_html
        
        # Step 1: Remove unwanted tags entirely
        TAGS_TO_REMOVE = {'script', 'style', 'noscript', 'iframe', 'meta', 'link', 'img', 'svg'}
        for tag in soup.find_all(TAGS_TO_REMOVE):
            try:
                tag.decompose()
            except Exception as e:
                logger.warning(f"Failed to remove tag {tag.name}: {str(e)}")
        
        # Step 2: Remove elements related to templates, themes, or frameworks
        for el in soup.find_all():
            if el is None:
                continue
                
            try:
                # Class or ID matches unwanted terms
                if any(
                    attr_val
                    for attr in [el.get('class', []), el.get('id', '')]
                    if attr and any(term in str(attr).lower() for term in TEMPLATE_TERMS)
                ):
                    el.decompose()
                    continue
            
                # Has template/theme specific attributes
                if any(el.has_attr(attr) for attr in ['data-template', 'data-theme']):
                    el.decompose()
                    continue
            
                # Path-based removals from src/href
                for attr in ['src', 'href']:
                    val = el.get(attr, '').lower()
                    if '?' in val and any(c.isdigit() for c in val.split('?')[1]):
                        el.decompose()
                        break
                    if any(path in val for path in MEDIA_PATHS):
                        el.decompose()
                        break
            except Exception as e:
                logger.warning(f"Failed to process element: {str(e)}")
                continue
        
        # Step 3: Remove ad and analytics blocks by class
        for el in soup.find_all(class_=lambda x: x and any(term in str(x).lower() for term in AD_TERMS)):
            try:
                el.decompose()
            except Exception as e:
                logger.warning(f"Failed to remove ad block: {str(e)}")
        
        # Step 4: Strip attributes related to styles, layouts, accessibility, and roles
        for el in soup.find_all():
            if el is None or not hasattr(el, 'attrs'):
                continue
                
            try:
                attrs_to_remove = []
                for attr in list(el.attrs.keys()):
                    if (
                        attr in {'style', 'class', 'id', 'role'} or
                        attr.startswith('data-') or
                        attr.startswith('aria-') or
                        attr in STYLE_ATTRIBUTES or
                        any(term in attr.lower() for term in ['style', 'color', 'font', 'size', 'width', 'height', 'margin', 'padding', 'border', 'background'])
                    ):
                        attrs_to_remove.append(attr)
                for attr in attrs_to_remove:
                    del el[attr]
            
                # Remove completely empty elements
                if not el.get_text(strip=True):
                    el.decompose()
            except Exception as e:
                logger.warning(f"Failed to process element attributes: {str(e)}")
                continue
        
        # Step 5: Remove empty/spacing-only divs and spans
        for el in soup.find_all(['div', 'span', 'p']):
            if el is None:
                continue
                
            try:
                el_str = str(el).lower()
                if not el.get_text(strip=True) or any(term in el_str for term in [
                    'margin', 'padding', 'spacing', 'font-size', 'text-align', 'display: block'
                ]):
                    el.decompose()
            except Exception as e:
                logger.warning(f"Failed to process spacing element: {str(e)}")
                continue
        
        return str(soup)
        
    except Exception as e:
        logger.error(f"HTML cleanup failed: {str(e)}")
        return html_content

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

        # Set up session with retry mechanism
        session = requests.Session()
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Step 1: Fetch the web page with proper headers
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

        try:
            response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            click.echo(click.style(f"😢 Error accessing the website: {str(e)}", fg='red'))
            return
        finally:
            session.close()

        # Debug: Check response content
        click.echo(click.style(f"\nResponse status: {response.status_code}", fg='blue'))
        click.echo(click.style(f"Response length: {len(response.text)} characters", fg='blue'))

        # Get the raw HTML content and clean it
        html_content = response.text
        cleaned_html = clean_html_content(html_content)
        
        if not cleaned_html:
            click.echo(click.style("No content could be extracted from the page.", fg='red'))
            return

        # Debug: Show content lengths and sample
        click.echo(click.style(f"Original HTML length: {len(html_content)} characters", fg='blue'))
        click.echo(click.style(f"Cleaned HTML length: {len(cleaned_html)} characters", fg='blue'))
        click.echo(click.style("\nSample of cleaned HTML:", fg='blue'))
        click.echo(click.style(cleaned_html[:MAX_SAMPLE_LENGTH] + "...", fg='blue'))

        # Step 3: Prepare the prompt for GPT-4
        current_time = datetime.now().strftime("%I:%M %p")
        prompt = f"""
You are helping a golfer find the next available tee time on a golf course website. You will be given cleaned HTML content to parse.

Current time: {current_time}

Below is the cleaned HTML content of a golf-related website page:
{cleaned_html[:MAX_HTML_LENGTH]}

Your task:
1. Parse the HTML and look for the next available tee time on this page. If you find it, format it as:
   NEXT TEE TIME:
   - Time: [exact time]
   - Available for: [number of players]
   - Price: [if available]
   - Notes: [any important information]

2. If you don't find a tee time on this page, analyze the HTML and find links that might lead to a tee time booking page. Look for:
   - Links containing words like "tee time", "book", "reserve", "schedule", "golf", "play"
   - Links that appear to be booking buttons or navigation items
   - Links that are prominently displayed or in the main navigation
   
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

    except requests.exceptions.Timeout:
        click.echo(click.style("⏰ Request timed out. The website might be slow or blocking our requests.", fg='red'))
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"Error accessing the website: {str(e)}", fg='red'))
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