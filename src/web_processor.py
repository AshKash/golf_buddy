# web_processor.py

from playwright.sync_api import sync_playwright
import logging
from html_to_md import html_to_markdown
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_visible_rendered_html(
    url: str,
    browser_args: Optional[List[str]] = None,
    viewport: Optional[Dict[str, int]] = None,
    user_agent: Optional[str] = None,
    timeout: int = 30000
) -> str:
    """
    Use Playwright to fetch fully rendered HTML of a web page,
    then convert it to clean Markdown.
    
    Args:
        url (str): The URL to fetch and process
        browser_args (List[str], optional): Browser launch arguments
        viewport (Dict[str, int], optional): Browser viewport settings
        user_agent (str, optional): Browser user agent string
        timeout (int, optional): Page timeout in milliseconds
        
    Returns:
        str: The converted Markdown content
    """
    try:
        with sync_playwright() as p:
            # Launch browser with provided settings
            browser = p.chromium.launch(
                headless=True,
                args=browser_args or []
            )
            
            # Create context with provided settings
            context = browser.new_context(
                viewport=viewport or {"width": 1920, "height": 1080},
                user_agent=user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            # Create new page
            page = context.new_page()
            page.set_default_timeout(timeout)
            
            try:
                # Navigate and wait for network idle
                logger.info(f"Navigating to {url}")
                response = page.goto(url, wait_until='networkidle')
                
                if not response or not response.ok:
                    logger.error(f"Failed to load page: {response.status if response else 'No response'}")
                    return ""
                
                # Wait a bit more for any dynamic content
                page.wait_for_timeout(2000)
                
                # Get the rendered HTML
                html = page.content()
                logger.info(f"Successfully fetched HTML (length: {len(html)})")
                
                # Convert HTML to Markdown
                markdown = html_to_markdown(html)
                logger.info(f"Successfully converted to Markdown (length: {len(markdown)})")
                return markdown
                
            finally:
                # Clean up
                page.close()
                context.close()
                browser.close()
                
    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        return ""