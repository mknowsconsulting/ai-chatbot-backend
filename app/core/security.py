"""
Security Module
Handles JWT tokens, password hashing, and authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================
# PASSWORD HASHING
# ============================================

def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
        
    Note:
        Bcrypt has a 72-byte limit. Passwords are truncated if longer.
    """
    # Bcrypt has 72-byte limit, truncate if necessary
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against hashed password
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Truncate if necessary (same as hash_password)
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# ============================================
# JWT TOKEN MANAGEMENT
# ============================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Dictionary of claims to encode in token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
        
    Example:
        token = create_access_token({
            "user_id": 1,
            "nim": "12345",
            "role": "student"
        })
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.APP_NAME
    })
    
    # Encode JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify JWT access token
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary of decoded claims or None if invalid
        
    Example:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("user_id")
            role = payload.get("role")
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return None


def verify_token(token: str) -> bool:
    """
    Verify if token is valid (not expired, correct signature)
    
    Args:
        token: JWT token string
        
    Returns:
        True if valid, False otherwise
    """
    payload = decode_access_token(token)
    return payload is not None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get expiration datetime from token
    
    Args:
        token: JWT token string
        
    Returns:
        Expiration datetime or None if invalid
    """
    payload = decode_access_token(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None


# ============================================
# ROLE EXTRACTION
# ============================================

def get_user_role_from_token(token: str) -> Optional[str]:
    """
    Extract user role from JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        User role (public, student, admin) or None
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("role")
    return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Extract user ID from JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        User ID or None
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("user_id")
    return None


def get_student_nim_from_token(token: str) -> Optional[str]:
    """
    Extract student NIM from JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Student NIM or None
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("nim")
    return None


# ============================================
# ADMIN TOKEN CREATION
# ============================================

def create_admin_token(admin_id: int, username: str, email: str) -> str:
    """
    Create JWT token for admin user
    
    Args:
        admin_id: Admin user ID
        username: Admin username
        email: Admin email
        
    Returns:
        JWT token string
    """
    return create_access_token({
        "user_id": admin_id,
        "username": username,
        "email": email,
        "role": "admin"
    })


def create_student_token(
    user_id: int,
    nim: str,
    name: str,
    jurusan: str,
    semester: int
) -> str:
    """
    Create JWT token for student user
    
    Args:
        user_id: Student user ID in LMS
        nim: Student NIM
        name: Student full name
        jurusan: Student major/program
        semester: Current semester
        
    Returns:
        JWT token string
    """
    return create_access_token({
        "user_id": user_id,
        "nim": nim,
        "name": name,
        "jurusan": jurusan,
        "semester": semester,
        "role": "student"
    })


# ============================================
# UTILITY FUNCTIONS
# ============================================

def extract_bearer_token(authorization: str) -> Optional[str]:
    """
    Extract token from Authorization header
    
    Args:
        authorization: Authorization header value (e.g., "Bearer eyJ...")
        
    Returns:
        Token string or None
        
    Example:
        token = extract_bearer_token("Bearer eyJhbGc...")
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


def is_token_expired(token: str) -> bool:
    """
    Check if token is expired
    
    Args:
        token: JWT token string
        
    Returns:
        True if expired, False otherwise
    """
    expiry = get_token_expiry(token)
    if expiry:
        return datetime.utcnow() > expiry
    return True
