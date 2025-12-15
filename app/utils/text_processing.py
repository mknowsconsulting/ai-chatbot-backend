"""
Text Processing Utilities
Helper functions for text manipulation, cleaning, and normalization
"""

import re
from typing import Optional
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize text: lowercase, remove extra spaces, trim
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Trim
    text = text.strip()
    
    return text


def clean_question(question: str) -> str:
    """
    Clean user question for FAQ matching
    
    Args:
        question: User's question
        
    Returns:
        Cleaned question
    """
    # Normalize
    question = normalize_text(question)
    
    # Remove punctuation except question marks
    question = re.sub(r'[^\w\s?]', '', question)
    
    # Remove multiple question marks
    question = re.sub(r'\?+', '?', question)
    
    return question


def extract_keywords(text: str, min_length: int = 3) -> list:
    """
    Extract keywords from text
    
    Args:
        text: Input text
        min_length: Minimum keyword length
        
    Returns:
        List of keywords
    """
    # Normalize
    text = normalize_text(text)
    
    # Split into words
    words = text.split()
    
    # Filter by length and remove common stop words
    stop_words = {'yang', 'di', 'ke', 'dari', 'untuk', 'dengan', 'adalah', 'ini', 'itu', 'the', 'is', 'at', 'to', 'a', 'an', 'and', 'or'}
    keywords = [w for w in words if len(w) >= min_length and w not in stop_words]
    
    return keywords


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].strip() + suffix


def remove_special_characters(text: str, keep_spaces: bool = True) -> str:
    """
    Remove special characters from text
    
    Args:
        text: Input text
        keep_spaces: Whether to keep spaces
        
    Returns:
        Cleaned text
    """
    if keep_spaces:
        pattern = r'[^a-zA-Z0-9\s]'
    else:
        pattern = r'[^a-zA-Z0-9]'
    
    return re.sub(pattern, '', text)


def slugify(text: str) -> str:
    """
    Convert text to slug (URL-friendly)
    
    Args:
        text: Input text
        
    Returns:
        Slugified text
        
    Example:
        slugify("Berapa Biaya Kuliah?") -> "berapa-biaya-kuliah"
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Trim hyphens
    text = text.strip('-')
    
    return text


def count_tokens_estimate(text: str) -> int:
    """
    Estimate token count for text (rough approximation)
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
        
    Note:
        This is a rough estimate. Actual token count may vary.
        Rule of thumb: 1 token ≈ 4 characters for English
    """
    # Simple estimation: words + punctuation
    words = len(text.split())
    chars = len(text)
    
    # Average: 1 token per 4 characters
    estimated_tokens = max(words, chars // 4)
    
    return estimated_tokens
