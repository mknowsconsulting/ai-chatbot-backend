"""
Security Middleware
Input validation, sanitization, and security headers
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import re
import logging

logger = logging.getLogger(__name__)

# Dangerous patterns for injection attacks
DANGEROUS_PATTERNS = [
    r"<script[^>]*>.*?</script>",  # XSS
    r"javascript:",  # XSS
    r"on\w+\s*=",  # Event handlers
    r"(union|select|insert|update|delete|drop|create|alter|exec|execute)\s+",  # SQL injection
    r"\.\./",  # Path traversal
    r"\.\.\\",  # Path traversal (Windows)
]

MAX_MESSAGE_LENGTH = 2000
MAX_SESSION_ID_LENGTH = 100


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security checks and headers"""
    
    async def dispatch(self, request: Request, call_next):
        # Add security headers to response
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        text: User input string
        
    Returns:
        Sanitized string
    """
    if not text:
        return text
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit length
    if len(text) > MAX_MESSAGE_LENGTH:
        text = text[:MAX_MESSAGE_LENGTH]
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Dangerous pattern detected: {pattern}")
            raise HTTPException(
                status_code=400,
                detail="Invalid input detected"
            )
    
    return text.strip()


def validate_session_id(session_id: str) -> str:
    """
    Validate session ID format
    
    Args:
        session_id: Session ID string
        
    Returns:
        Validated session ID
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Check length
    if len(session_id) > MAX_SESSION_ID_LENGTH:
        raise HTTPException(status_code=400, detail="Session ID too long")
    
    # Only allow alphanumeric, dash, underscore
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    return session_id


def validate_nim(nim: str) -> str:
    """
    Validate NIM format
    
    Args:
        nim: Student NIM
        
    Returns:
        Validated NIM
    """
    if not nim:
        raise HTTPException(status_code=400, detail="NIM required")
    
    # Remove whitespace
    nim = nim.strip()
    
    # Check length (typical NIM is 8-15 digits)
    if len(nim) < 5 or len(nim) > 20:
        raise HTTPException(status_code=400, detail="Invalid NIM format")
    
    # Only allow alphanumeric
    if not re.match(r'^[a-zA-Z0-9]+$', nim):
        raise HTTPException(status_code=400, detail="Invalid NIM format")
    
    return nim


def validate_password(password: str) -> str:
    """
    Validate password requirements
    
    Args:
        password: User password
        
    Returns:
        Validated password
    """
    if not password:
        raise HTTPException(status_code=400, detail="Password required")
    
    # Check length
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password too short")
    
    if len(password) > 128:
        raise HTTPException(status_code=400, detail="Password too long")
    
    return password
