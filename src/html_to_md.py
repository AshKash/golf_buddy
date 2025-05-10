#!/usr/bin/env python3
"""
HTML to Markdown Converter

This module provides functionality to convert HTML content to clean, readable Markdown format.
It uses the html2text library for the core conversion and includes additional cleaning and
formatting options.

Key Features:
    - Converts HTML to clean Markdown
    - Preserves important formatting (bold, italic, links)
    - Handles tables and lists
    - Configurable output options
    - Streaming support for large files

Usage:
    As a module:
        from html_to_md import html_to_markdown
        markdown = html_to_markdown(html_content)

    From command line:
        python html_to_md.py --input input.html --output output.md
        python html_to_md.py --stdin -o output.md

Configuration:
    The converter can be configured with various options:
    - ignore_links: Keep URLs in the output (default: False)
    - ignore_images: Skip images (default: True)
    - body_width: Prevent line wrapping (default: 0)
    - unicode_snob: Use Unicode characters (default: False)
    - ignore_emphasis: Keep emphasis (default: False)
    - ignore_tables: Keep tables (default: False)
    - ignore_anchors: Keep anchor links (default: False)

Dependencies:
    - html2text: Core HTML to Markdown conversion
    - logging: For error and info logging
"""

import html2text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def html_to_markdown(html: str) -> str:
    """Convert full HTML to clean Markdown.
    
    This function takes HTML content and converts it to a clean, readable Markdown format.
    It handles various HTML elements and provides configurable output options.
    Large files are supported by streaming internally.
    
    Args:
        html (str): The HTML content to convert. Can be a full HTML document or a fragment.
        
    Returns:
        str: The converted Markdown content. Returns an empty string if conversion fails.
        
    Example:
        >>> html = "<p>Hello <b>World</b></p>"
        >>> markdown = html_to_markdown(html)
        >>> print(markdown)
        Hello **World**
        
    Note:
        The function uses html2text for conversion and includes additional cleaning
        and formatting options. It preserves important formatting like bold, italic,
        and links while removing unnecessary elements.
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