import re
import logging
from bs4 import BeautifulSoup
from nltk.util import clean_html

# Set up logging
logger = logging.getLogger(__name__)

# Constants
TAGS_TO_REMOVE = {'script', 'style', 'noscript', 'iframe', 'meta', 'link', 'img', 'svg'}
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

def remove_unwanted_tags(soup: BeautifulSoup) -> None:
    """Remove unwanted HTML tags from the soup."""
    for tag in soup.find_all(TAGS_TO_REMOVE):
        try:
            tag.decompose()
        except Exception as e:
            logger.warning(f"Failed to remove tag {tag.name}: {str(e)}")

def remove_template_elements(soup: BeautifulSoup) -> None:
    """Remove elements related to templates, themes, or frameworks."""
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

def remove_ad_blocks(soup: BeautifulSoup) -> None:
    """Remove ad and analytics blocks by class."""
    for el in soup.find_all(class_=lambda x: x and any(term in str(x).lower() for term in AD_TERMS)):
        try:
            el.decompose()
        except Exception as e:
            logger.warning(f"Failed to remove ad block: {str(e)}")

def strip_style_attributes(soup: BeautifulSoup) -> None:
    """Strip attributes related to styles, layouts, accessibility, and roles."""
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

def remove_spacing_elements(soup: BeautifulSoup) -> None:
    """Remove empty/spacing-only divs and spans."""
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

def clean_whitespace(soup: BeautifulSoup) -> str:
    """Clean up whitespace and format HTML."""
    # Remove extra whitespace from text nodes
    for text in soup.find_all(text=True):
        if text.parent.name not in ['pre', 'code']:  # Preserve whitespace in pre/code blocks
            text.replace_with(' '.join(text.split()))

    # Remove empty lines and normalize spacing
    html_str = str(soup)
    # Remove blank lines
    html_str = '\n'.join(line for line in html_str.splitlines() if line.strip())
    # Remove extra spaces between tags
    html_str = re.sub(r'>\s+<', '><', html_str)
    # Add newlines after major tags for readability
    html_str = re.sub(r'(<[^/][^>]*>)', r'\1\n', html_str)
    html_str = re.sub(r'(</[^>]*>)', r'\1\n', html_str)
    # Remove multiple consecutive newlines
    html_str = re.sub(r'\n\s*\n', '\n', html_str)
    # Remove leading/trailing whitespace
    html_str = html_str.strip()
    
    return html_str

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
        
        # Apply all cleaning steps
        remove_unwanted_tags(soup)
        remove_template_elements(soup)
        remove_ad_blocks(soup)
        strip_style_attributes(soup)
        remove_spacing_elements(soup)
        
        # Final formatting
        return clean_whitespace(soup)
        
    except Exception as e:
        logger.error(f"HTML cleanup failed: {str(e)}")
        return html_content 