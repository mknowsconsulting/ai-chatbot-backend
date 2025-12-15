"""
Helper Functions
General utility functions used across the application
"""

from datetime import datetime, date
from typing import Optional, Any, Dict
import uuid
import json
import hashlib


def generate_session_id() -> str:
    """
    Generate unique session ID
    
    Returns:
        Session ID string (e.g., "sess_abc123...")
    """
    unique_id = str(uuid.uuid4())
    return f"sess_{unique_id.replace('-', '')[:16]}"


def generate_uuid() -> str:
    """
    Generate UUID v4
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format
    
    Returns:
        ISO formatted timestamp
    """
    return datetime.utcnow().isoformat()


def get_current_date() -> str:
    """
    Get current date (YYYY-MM-DD)
    
    Returns:
        Date string
    """
    return date.today().isoformat()


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string
    
    Args:
        dt: Datetime object
        format_str: Format string
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse datetime string to datetime object
    
    Args:
        dt_str: Datetime string
        format_str: Format string
        
    Returns:
        Datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except Exception:
        return None


def safe_dict_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary
    
    Args:
        dictionary: Dictionary to search
        key: Key to find
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    return dictionary.get(key, default)


def dict_to_json(data: Dict[str, Any], pretty: bool = False) -> str:
    """
    Convert dictionary to JSON string
    
    Args:
        data: Dictionary to convert
        pretty: Whether to format JSON prettily
        
    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    return json.dumps(data, ensure_ascii=False)


def json_to_dict(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Convert JSON string to dictionary
    
    Args:
        json_str: JSON string
        
    Returns:
        Dictionary or None if parsing fails
    """
    try:
        return json.loads(json_str)
    except Exception:
        return None


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using specified algorithm
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        Hashed string (hex digest)
    """
    if algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text.encode()).hexdigest()
    else:  # default sha256
        return hashlib.sha256(text.encode()).hexdigest()


def calculate_cost(tokens: int, cost_per_1m_tokens: float = 0.14) -> float:
    """
    Calculate API cost based on token usage
    
    Args:
        tokens: Number of tokens used
        cost_per_1m_tokens: Cost per 1 million tokens (DeepSeek: $0.14/$0.28)
        
    Returns:
        Cost in USD
        
    Example:
        cost = calculate_cost(1000)  # Cost for 1000 tokens
    """
    return (tokens / 1_000_000) * cost_per_1m_tokens


def chunks(lst: list, n: int):
    """
    Yield successive n-sized chunks from list
    
    Args:
        lst: List to chunk
        n: Chunk size
        
    Yields:
        Chunks of size n
        
    Example:
        for chunk in chunks([1,2,3,4,5], 2):
            print(chunk)  # [1,2], [3,4], [5]
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def is_valid_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email string
        
    Returns:
        True if valid email format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_nim(nim: str) -> bool:
    """
    Validate NIM format (customizable based on your rules)
    
    Args:
        nim: NIM string
        
    Returns:
        True if valid NIM format
    """
    # Example: NIM should be numeric and 5-20 digits
    return nim.isdigit() and 5 <= len(nim) <= 20
