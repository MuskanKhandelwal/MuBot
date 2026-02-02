"""
Helper Utilities

General-purpose helper functions for text processing, ID generation,
date formatting, and file handling.
"""

import hashlib
import re
import uuid
from datetime import datetime
from typing import Optional


def generate_id() -> str:
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


def generate_short_id(text: str, length: int = 8) -> str:
    """
    Generate a short hash ID from text.
    
    Args:
        text: Input text to hash
        length: Length of output hash
    
    Returns:
        Short hash string
    """
    hash_obj = hashlib.md5(text.encode())
    return hash_obj.hexdigest()[:length]


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format datetime for display.
    
    Args:
        dt: Datetime to format
        format_str: strftime format string
    
    Returns:
        Formatted string or "N/A" if dt is None
    """
    if not dt:
        return "N/A"
    return dt.strftime(format_str)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string for use as a filename.
    
    Removes or replaces characters that are invalid in filenames.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized


def html_to_text(html: str) -> str:
    """
    Simple HTML to plain text conversion.
    
    Args:
        html: HTML string
    
    Returns:
        Plain text
    """
    # Remove script and style elements
    text = re.sub(r'<(script|style)[^>]*>[^<]*</\1>', '', html, flags=re.IGNORECASE)
    
    # Replace common block elements with newlines
    text = re.sub(r'</(div|p|h[1-6]|li)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common entities
    entities = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&#39;': "'",
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)
    
    # Normalize whitespace
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    
    return text


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def estimate_reading_time(text: str, wpm: int = 200) -> int:
    """
    Estimate reading time in seconds.
    
    Args:
        text: Text to estimate
        wpm: Words per minute reading speed
    
    Returns:
        Estimated seconds to read
    """
    words = count_words(text)
    seconds = (words / wpm) * 60
    return max(1, int(seconds))


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Return singular or plural form based on count.
    
    Args:
        count: Number
        singular: Singular form
        plural: Plural form (default: singular + 's')
    
    Returns:
        Appropriate form
    """
    if count == 1:
        return f"{count} {singular}"
    
    plural = plural or f"{singular}s"
    return f"{count} {plural}"
