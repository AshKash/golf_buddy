import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup, Comment
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for hidden elements
HIDDEN_KEYWORDS = {
    'hidden', 'banner', 'popup', 'modal', 'overlay', 'ads', 'track', 'cookie',
    'notification', 'alert', 'tooltip', 'menu', 'sidebar', 'footer', 'header',
    'nav', 'navigation', 'social', 'share', 'comment', 'related', 'recommended'
}

UNWANTED_TAGS = {
    'script', 'style', 'noscript', 'iframe', 'svg', 'link', 'meta',
    'head', 'path', 'img', 'picture', 'source', 'video', 'audio',
    'canvas', 'embed', 'object', 'param', 'track'
}

def get_visible_rendered_html(url: str) -> str:
    """Fetch rendered HTML from a URL and return only what's visible to the user."""
    try:
        with sync_playwright() as p:
            # Launch browser with additional options
            browser = p.chromium.launch(
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
            
            # Create a new context with specific viewport and user agent
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            # Create a new page
            page = context.new_page()
            
            # Set default timeout
            page.set_default_timeout(30000)  # 30 seconds
            
            try:
                # Navigate and wait for network to be idle
                logger.info(f"Navigating to {url}")
                response = page.goto(url, wait_until='networkidle', timeout=30000)
                
                if not response:
                    logger.error("Failed to get response from page")
                    return ""
                
                if not response.ok:
                    logger.error(f"Page returned status code: {response.status}")
                    return ""
                
                # Wait a bit more for any dynamic content
                page.wait_for_timeout(2000)
                
                # Get fully rendered HTML
                rendered_html = page.content()
                
                if not rendered_html:
                    logger.error("No HTML content received from page")
                    return ""
                
            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout while loading page: {str(e)}")
                return ""
            except Exception as e:
                logger.error(f"Error during page navigation: {str(e)}")
                return ""
            finally:
                # Clean up
                context.close()
                browser.close()
            
        # Parse with BeautifulSoup
        soup = BeautifulSoup(rendered_html, 'html.parser')
        
        # Remove comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove unwanted tags
        for tag in soup.find_all(UNWANTED_TAGS):
            tag.decompose()
        
        # Remove elements hidden via inline styles
        for el in soup.find_all(style=True):
            style = el['style'].lower()
            if any(term in style for term in ['display:none', 'visibility:hidden', 'opacity:0']):
                el.decompose()
        
        # Remove elements by class/id names
        for el in soup.find_all():
            if el is None:
                continue
                
            # Get class and id as strings
            classes = ' '.join(el.get('class', []))
            el_id = el.get('id', '')
            class_id = f"{classes} {el_id}".lower()
            
            # Remove if element has hidden keywords
            if any(keyword in class_id for keyword in HIDDEN_KEYWORDS):
                el.decompose()
                continue
            
            # Remove empty elements
            if not el.get_text(strip=True):
                el.decompose()
        
        # Clean up whitespace
        for text in soup.find_all(text=True):
            if text.parent.name not in ['pre', 'code']:
                text.replace_with(text.strip())
        
        # Get final HTML
        clean_html = str(soup)
        
        # Remove extra whitespace
        clean_html = ' '.join(clean_html.split())
        
        return clean_html
        
    except Exception as e:
        logger.error(f"Error fetching HTML: {str(e)}")
        return "" 