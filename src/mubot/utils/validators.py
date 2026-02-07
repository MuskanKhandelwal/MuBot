"""
Validation Utilities

Input validation functions for emails, URLs, and other data types.
"""

import re
from urllib.parse import urlparse


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid format
    """
    if not email or "@" not in email:
        return False
    
    # Basic regex for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str, allowed_schemes: list[str] = None) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: http, https)
    
    Returns:
        True if valid
    """
    if not url:
        return False
    
    allowed_schemes = allowed_schemes or ["http", "https"]
    
    try:
        parsed = urlparse(url)
        return parsed.scheme in allowed_schemes and bool(parsed.netloc)
    except Exception:
        return False

