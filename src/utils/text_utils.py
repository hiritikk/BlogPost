"""
Text utility functions for blog processing
"""
import re
from typing import List
import unicodedata

def generate_slug(title: str) -> str:
    """
    Generate a URL-friendly slug from a title
    
    Args:
        title: The blog post title
        
    Returns:
        URL-friendly slug
    """
    # Convert to lowercase
    slug = title.lower()
    
    # Remove accents
    slug = unicodedata.normalize('NFKD', slug)
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Limit length
    if len(slug) > 100:
        slug = slug[:100].rsplit('-', 1)[0]
    
    return slug

def count_words(text: str) -> int:
    """
    Count the number of words in a text
    
    Args:
        text: The text to count words in
        
    Returns:
        Number of words
    """
    # Remove markdown formatting
    text = re.sub(r'[#*_\[\]()]', '', text)
    
    # Split by whitespace and count
    words = text.split()
    return len(words)

def estimate_reading_time(text: str, wpm: int = 200) -> int:
    """
    Estimate reading time in minutes
    
    Args:
        text: The text to estimate reading time for
        wpm: Words per minute (default: 200)
        
    Returns:
        Estimated reading time in minutes
    """
    word_count = count_words(text)
    reading_time = word_count / wpm
    
    # Round up to nearest minute
    return max(1, round(reading_time))

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text
    
    Args:
        text: The text to extract keywords from
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of keywords
    """
    # Simple keyword extraction based on frequency
    # Remove common words
    stop_words = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
        'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this',
        'it', 'from', 'be', 'are', 'been', 'was', 'were', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'could'
    }
    
    # Convert to lowercase and split
    words = text.lower().split()
    
    # Remove punctuation and stop words
    words = [re.sub(r'[^a-z0-9]', '', word) for word in words]
    words = [word for word in words if word and word not in stop_words and len(word) > 3]
    
    # Count frequency
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, freq in sorted_words[:max_keywords]]
    
    return keywords

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length
    
    Args:
        text: The text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + suffix

def clean_html(text: str) -> str:
    """
    Remove HTML tags from text
    
    Args:
        text: Text with potential HTML tags
        
    Returns:
        Clean text without HTML
    """
    return re.sub(r'<[^>]+>', '', text)

def format_citation(source: dict, style: str = "apa") -> str:
    """
    Format a citation based on the given style
    
    Args:
        source: Source information dictionary
        style: Citation style (apa, mla, chicago)
        
    Returns:
        Formatted citation
    """
    author = source.get('author', 'Unknown Author')
    title = source.get('title', 'Untitled')
    year = source.get('publication_date', '').split('-')[0] if source.get('publication_date') else 'n.d.'
    url = source.get('url', '')
    
    if style == "apa":
        citation = f"{author} ({year}). {title}."
        if url:
            citation += f" Retrieved from {url}"
    elif style == "mla":
        citation = f'{author}. "{title}."'
        if url:
            citation += f" Web. {url}"
    else:  # chicago
        citation = f'{author}. "{title}."'
        if url:
            citation += f" Accessed from {url}"
    
    return citation 