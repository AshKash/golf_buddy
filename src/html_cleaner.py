import re
import logging
from bs4 import BeautifulSoup, Comment

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for HTML cleaning
UNWANTED_TAGS = {
    'script', 'style', 'noscript', 'iframe', 'meta', 'link', 'head',
    'svg', 'path', 'img', 'picture', 'source', 'video', 'audio',
    'canvas', 'embed', 'object', 'param', 'track'
}

TEMPLATE_INDICATORS = {
    'template', 'component', 'widget', 'module', 'section',
    'header', 'footer', 'nav', 'sidebar', 'menu'
}

AD_INDICATORS = {
    'ad', 'advertisement', 'banner', 'sponsored', 'promo',
    'analytics', 'tracking', 'pixel', 'beacon'
}

STYLE_ATTRIBUTES = {
    'style', 'class', 'id', 'color', 'font', 'size', 'width', 'height',
    'margin', 'padding', 'border', 'background', 'position', 'display',
    'float', 'clear', 'visibility', 'opacity', 'z-index', 'text-align',
    'font-family', 'font-size', 'font-weight', 'font-style', 'line-height',
    'text-decoration', 'text-transform', 'letter-spacing', 'word-spacing',
    'vertical-align', 'white-space', 'overflow', 'text-overflow', 'box-shadow',
    'transition', 'animation', 'transform', 'filter', 'backdrop-filter'
}

# Add form state elements to remove
FORM_STATE_ATTRIBUTES = {
    '__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION',
    '__EVENTTARGET', '__EVENTARGUMENT', '__LASTFOCUS',
    '__VIEWSTATEENCRYPTED', '__PREVIOUSPAGE'
}

def remove_unwanted_tags(soup):
    """Remove unwanted HTML tags."""
    if not soup:
        return soup
    for tag in soup.find_all(UNWANTED_TAGS):
        if tag is not None:
            tag.decompose()
    return soup

def remove_template_elements(soup):
    """Remove template-related elements."""
    if not soup:
        return soup
    for el in soup.find_all():
        if el is None:
            continue
        # Check class and id for template indicators
        classes = el.get('class', []) if hasattr(el, 'get') else []
        el_id = el.get('id', '') if hasattr(el, 'get') else ''
        
        # Remove if element has template-related classes or IDs
        if any(indicator in str(classes).lower() or indicator in str(el_id).lower() 
               for indicator in TEMPLATE_INDICATORS):
            el.decompose()
    return soup

def remove_ad_blocks(soup):
    """Remove ad and analytics blocks."""
    if not soup:
        return soup
    for el in soup.find_all():
        if el is None or not hasattr(el, 'attrs'):
            continue
        # Check class, id, and data attributes for ad indicators
        classes = el.get('class', []) if hasattr(el, 'get') else []
        el_id = el.get('id', '') if hasattr(el, 'get') else ''
        data_attrs = [attr for attr in el.attrs if attr.startswith('data-')] if hasattr(el, 'attrs') else []
        
        # Remove if element has ad-related indicators
        if any(indicator in str(classes).lower() or 
               indicator in str(el_id).lower() or
               any(indicator in str(el.get(attr, '')).lower() for attr in data_attrs)
               for indicator in AD_INDICATORS):
            el.decompose()
    return soup

def remove_form_state(soup):
    """Remove hidden form fields and other form state elements."""
    if not soup:
        return soup
        
    # Remove hidden input fields
    for input_field in soup.find_all('input', type='hidden'):
        if input_field is None:
            continue
            
        # Check if it's a state-related field
        field_id = input_field.get('id', '')
        field_name = input_field.get('name', '')
        
        if any(state_term in str(field_id).lower() or state_term in str(field_name).lower() 
               for state_term in FORM_STATE_ATTRIBUTES):
            input_field.decompose()
            
    # Remove other form state elements
    for el in soup.find_all():
        if el is None:
            continue
            
        # Check for state-related IDs or names
        el_id = el.get('id', '')
        el_name = el.get('name', '')
        
        if any(state_term in str(el_id).lower() or state_term in str(el_name).lower() 
               for state_term in FORM_STATE_ATTRIBUTES):
            el.decompose()
            
    return soup

def remove_inline_styles(soup):
    """Remove all inline styles and style-related attributes."""
    if not soup:
        return soup
        
    # Remove all style tags and their contents
    for style in soup.find_all('style'):
        style.decompose()
        
    # Remove elements with display:none or visibility:hidden
    for el in soup.find_all():
        if el is None or not hasattr(el, 'attrs'):
            continue
            
        # Check style attribute for display:none or visibility:hidden
        style = el.get('style', '')
        if style and any(term in style.lower() for term in ['display:none', 'visibility:hidden']):
            el.decompose()
            continue
            
        # Remove style attribute
        if 'style' in el.attrs:
            del el['style']
            
        # Remove all style-related attributes
        attrs_to_remove = []
        for attr in el.attrs:
            if any(style_term in attr.lower() for style_term in STYLE_ATTRIBUTES):
                attrs_to_remove.append(attr)
                
        for attr in attrs_to_remove:
            del el[attr]
            
        # Remove elements that are purely for styling
        if el.name in ['span', 'div'] and not el.get_text(strip=True):
            el.decompose()
            
    # Remove elements with specific classes that are typically used for styling
    styling_classes = {
        'wsc_switcher_control_panel', 'wsc_switcher_control', 'personalBarContainer',
        'menu-center', 'container', 'header'
    }
    
    for el in soup.find_all(class_=True):
        if el is None:
            continue
            
        classes = el.get('class', [])
        if any(styling_class in str(classes).lower() for styling_class in styling_classes):
            el.decompose()
            
    return soup

def strip_style_attributes(soup):
    """Strip style-related attributes from elements."""
    if not soup:
        return soup
    for el in soup.find_all():
        if el is None or not hasattr(el, 'attrs'):
            continue
            
        # Remove style-related attributes
        attrs_to_remove = []
        for attr in el.attrs:
            if any(style_term in attr.lower() for style_term in STYLE_ATTRIBUTES):
                attrs_to_remove.append(attr)
        
        for attr in attrs_to_remove:
            del el[attr]
    return soup

def remove_spacing_elements(soup):
    """Remove empty or spacing-only elements."""
    if not soup:
        return soup
    for el in soup.find_all(['span', 'div', 'p']):
        if el is None:
            continue
        # Remove if element is empty or contains only whitespace
        if not el.get_text(strip=True) if hasattr(el, 'get_text') else True:
            el.decompose()
            continue
            
        # Remove if element only contains spacing styles
        style = el.get('style', '') if hasattr(el, 'get') else ''
        if style and all(term in style.lower() for term in ['margin', 'padding', 'spacing']):
            el.decompose()
    return soup

def clean_whitespace(soup):
    """Clean up whitespace and format HTML."""
    if not soup:
        return ''
    # Remove extra whitespace from text nodes
    for text in soup.find_all(text=True):
        if text is None or text.parent is None:
            continue
        if text.parent.name not in ['script', 'style']:
            text.replace_with(text.strip())
    
    # Remove blank lines
    for el in soup.find_all():
        if el is None:
            continue
        if el.name in ['br', 'hr']:
            el.decompose()
    
    # Normalize spacing between tags
    html = str(soup)
    html = re.sub(r'>\s+<', '><', html)
    html = re.sub(r'\n\s*\n', '\n', html)
    
    return html

def clean_html_content(html_content):
    """Clean HTML content by removing unwanted elements, styling, and formatting."""
    if not html_content:
        logger.warning("Empty HTML content provided")
        return ""
        
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        if not soup:
            logger.warning("BeautifulSoup parsing returned None")
            return html_content
        
        # Remove comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            if comment is not None:
                comment.extract()
        
        # Remove all style tags first
        for style in soup.find_all('style'):
            style.decompose()
        
        # Apply cleaning steps
        soup = remove_unwanted_tags(soup)
        soup = remove_template_elements(soup)
        soup = remove_ad_blocks(soup)
        soup = remove_form_state(soup)
        soup = remove_inline_styles(soup)
        soup = strip_style_attributes(soup)
        soup = remove_spacing_elements(soup)
        
        # Clean whitespace and format
        cleaned_html = clean_whitespace(soup)
        
        return cleaned_html
        
    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        return html_content 