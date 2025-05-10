#!/usr/bin/env python3
"""
Web Processor - Handles web page fetching and processing.
"""

from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError
import logging
from .html_to_md import html_to_markdown
from typing import Optional
import time
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class WebProcessor:
    def __init__(self, headless: bool = None):
        """
        Initialize the WebProcessor with a Playwright browser instance.
        
        Args:
            headless: Whether to run the browser in headless mode.
                     If None, uses GOLF_BUDDY_HEADLESS env var or defaults to False.
        """
        if headless is None:
            headless = os.environ.get('GOLF_BUDDY_HEADLESS', 'false').lower() == 'true'
            
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,  # Use configured headless mode
            args=[
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--disable-blink-features=AutomationControlled'  # Hide automation
            ]
        )
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            java_script_enabled=True,
            bypass_csp=True,  # Bypass Content Security Policy
            ignore_https_errors=True  # Ignore HTTPS errors
        )
        # Add stealth scripts
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        logger.debug(f"WebProcessor initialized with browser instance (headless={headless})")

    def wait_for_cloudflare(self, page: Page, timeout: int = 30) -> bool:
        """
        Wait for Cloudflare verification to complete.
        
        Args:
            page (Page): The Playwright page object
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            bool: True if verification passed, False otherwise
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if we're still on the challenge page
                if page.url.startswith("https://challenges.cloudflare.com"):
                    time.sleep(2)
                    continue
                
                # Check if we've been redirected to the target page
                if not page.url.startswith("https://challenges.cloudflare.com"):
                    return True
                
                time.sleep(1)
            
            logger.error("Cloudflare verification timeout")
            return False
            
        except Exception as e:
            logger.error(f"Error during Cloudflare verification: {str(e)}")
            return False

    def wait_for_page_load(self, page: Page, timeout: int = 30) -> bool:
        """
        Wait for the page to load completely, including any redirects.
        
        Args:
            page (Page): The Playwright page object
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            bool: True if page loaded successfully, False otherwise
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Wait for network to be idle with a longer timeout
                    page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Check if we're on a valid page
                    if page.url and not page.url.startswith("https://challenges.cloudflare.com"):
                        # Wait for any Turnstile iframe to be handled
                        if page.url.startswith("https://cityofsunnyvale.ezlinksgolf.com"):
                            time.sleep(5)  # Give time for Turnstile to complete
                        
                        return True
                    
                    time.sleep(1)
                except TimeoutError:
                    # If networkidle times out, check if we're on a valid page
                    if page.url and not page.url.startswith("https://challenges.cloudflare.com"):
                        return True
                    continue
            
            logger.error("Page load timeout")
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for page load: {str(e)}")
            return False

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
                logger.info(f"Fetching content from: {url}")
                
                # First attempt to load the page
                response = page.goto(url, wait_until='domcontentloaded')
                
                if not response:
                    logger.error("No response received from page")
                    return ""
                
                # Check for Cloudflare challenge
                if response.status == 403 or 'cf-mitigated' in response.headers:
                    logger.info("Cloudflare challenge detected, waiting for verification...")
                    # Wait for the challenge to complete
                    if not self.wait_for_cloudflare(page):
                        logger.error("Failed to bypass Cloudflare verification")
                        return ""
                    
                    # Try to get the content again after verification
                    response = page.goto(url, wait_until='domcontentloaded')
                    if not response:
                        logger.error("No response after verification")
                        return ""
                
                # Wait for the page to load completely
                if not self.wait_for_page_load(page):
                    logger.error("Failed to load page completely")
                    return ""
                
                # Wait for any dynamic content
                page.wait_for_timeout(2000)
                
                # Get the rendered HTML
                html = page.content()
                
                # Convert HTML to Markdown
                markdown = html_to_markdown(html)
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
            if hasattr(self, 'context'):
                self.context.close()
            if hasattr(self, 'browser'):
                self.browser.close()
            if hasattr(self, 'playwright'):
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Error closing WebProcessor: {str(e)}")

# Global instance
_processor = None

def get_processor(headless: bool = None) -> WebProcessor:
    """
    Get or create the global WebProcessor instance.
    
    Args:
        headless: Whether to run the browser in headless mode.
                 If None, uses GOLF_BUDDY_HEADLESS env var or defaults to True.
    """
    global _processor
    if _processor is None:
        _processor = WebProcessor(headless=headless)
    return _processor

def get_visible_rendered_html(url: str, headless: bool = None) -> str:
    """
    Get the visible rendered HTML of a web page.
    
    Args:
        url: The URL to fetch and process
        headless: Whether to run the browser in headless mode.
                 If None, uses GOLF_BUDDY_HEADLESS env var or defaults to True.
    """
    processor = get_processor(headless=headless)
    return processor.get_visible_rendered_html(url)

def close_processor():
    """Close the global WebProcessor instance."""
    global _processor
    if _processor is not None:
        _processor.close()
        _processor = None
