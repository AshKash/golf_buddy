# web_processor.py

from playwright.sync_api import sync_playwright, Browser, Page
import logging
from html_to_md import html_to_markdown
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebProcessor:
    def __init__(self):
        """Initialize the WebProcessor with a Playwright browser instance."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions'
            ]
        )
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        logger.info("WebProcessor initialized with browser instance")

    def get_visible_rendered_html(self, url: str) -> str:
        """
        Use the initialized browser to fetch fully rendered HTML of a web page,
        then convert it to clean Markdown.
        
        Args:
            url (str): The URL to fetch and process
            
        Returns:
            str: The converted Markdown content
        """
        try:
            # Create new page
            page = self.context.new_page()
            page.set_default_timeout(30000)  # 30 second timeout
            
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
                # Clean up page
                page.close()
                
        except Exception as e:
            logger.error(f"Error processing URL: {str(e)}")
            return ""

    def close(self):
        """Clean up browser resources."""
        try:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            logger.info("WebProcessor resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Create a singleton instance
_processor = None

def get_processor() -> WebProcessor:
    """Get or create the singleton WebProcessor instance."""
    global _processor
    if _processor is None:
        _processor = WebProcessor()
    return _processor

def get_visible_rendered_html(url: str) -> str:
    """
    Convenience function to get rendered HTML using the singleton processor.
    
    Args:
        url (str): The URL to fetch and process
        
    Returns:
        str: The converted Markdown content
    """
    processor = get_processor()
    return processor.get_visible_rendered_html(url)