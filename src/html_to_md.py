# html_to_md.py

import html2text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def html_to_markdown(html: str) -> str:
    """
    Convert full HTML to clean Markdown.
    Large files are supported by streaming internally.
    
    Args:
        html (str): The HTML content to convert
        
    Returns:
        str: The converted Markdown content
    """
    try:
        if not html:
            logger.warning("Empty HTML content provided")
            return ""
            
        # Configure the converter
        converter = html2text.HTML2Text()
        converter.ignore_links = False  # Keep URLs in the output
        converter.ignore_images = True  # Skip images
        converter.body_width = 0        # Prevent line wrapping
        converter.unicode_snob = False  # Use Unicode characters
        converter.ignore_emphasis = False  # Keep emphasis (bold, italic)
        converter.ignore_tables = False    # Keep tables
        converter.ignore_anchors = False    # Keep anchor links
        
        # Convert HTML to Markdown
        markdown = converter.handle(html)
        
        # Clean up the output
        markdown = markdown.strip()
        
        logger.info(f"Successfully converted HTML to Markdown (length: {len(markdown)})")
        return markdown
        
    except Exception as e:
        logger.error(f"Error converting HTML to Markdown: {str(e)}")
        return "" 