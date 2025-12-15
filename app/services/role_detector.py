"""
Role Detection Service
Detect user role from JWT token or session
"""

from typing import Optional, Dict, Any
from fastapi import Request
import logging

from app.core.security import decode_access_token, extract_bearer_token

logger = logging.getLogger(__name__)


class RoleDetector:
    """
    Detect user role from request
    Roles: public, student, admin
    """
    
    def __init__(self):
        self.default_role = "public"
    
    def detect_from_request(self, request: Request) -> Dict[str, Any]:
        """
        Detect role from FastAPI request
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Dictionary with role and user info
            
        Example:
            role_info = detector.detect_from_request(request)
            # Returns:
            # {
            #     "role": "student",
            #     "user_id": 1,
            #     "nim": "12345",
            #     "name": "Budi Santoso"
            # }
        """
        
        # 1. Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if auth_header:
            token = extract_bearer_token(auth_header)
            if token:
                return self.detect_from_token(token)
        
        # 2. Try to get token from query params (alternative)
        token = request.query_params.get("token")
        if token:
            return self.detect_from_token(token)
        
        # 3. Default to public
        return {
            "role": self.default_role,
            "user_id": None,
            "authenticated": False
        }
    
    def detect_from_token(self, token: str) -> Dict[str, Any]:
        """
        Detect role from JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary with role and user info
        """
        
        # Decode token
        payload = decode_access_token(token)
        
        if not payload:
            logger.debug("Invalid token, using public role")
            return {
                "role": self.default_role,
                "user_id": None,
                "authenticated": False
            }
        
        # Extract role
        role = payload.get("role", self.default_role)
        
        # Build user info based on role
        if role == "student":
            return {
                "role": "student",
                "user_id": payload.get("user_id"),
                "nim": payload.get("nim"),
                "name": payload.get("name"),
                "jurusan": payload.get("jurusan"),
                "semester": payload.get("semester"),
                "authenticated": True
            }
        
        elif role == "admin":
            return {
                "role": "admin",
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "authenticated": True
            }
        
        else:  # public or unknown
            return {
                "role": "public",
                "user_id": None,
                "authenticated": False
            }
    
    def is_authenticated(self, role_info: Dict[str, Any]) -> bool:
        """Check if user is authenticated"""
        return role_info.get("authenticated", False)
    
    def is_student(self, role_info: Dict[str, Any]) -> bool:
        """Check if user is student"""
        return role_info.get("role") == "student"
    
    def is_admin(self, role_info: Dict[str, Any]) -> bool:
        """Check if user is admin"""
        return role_info.get("role") == "admin"
    
    def is_public(self, role_info: Dict[str, Any]) -> bool:
        """Check if user is public (not authenticated)"""
        return role_info.get("role") == "public"
    
    def get_user_identifier(self, role_info: Dict[str, Any]) -> str:
        """
        Get unique identifier for user (for rate limiting, history, etc.)
        
        Returns:
            - For student/admin: user_id
            - For public: session_id (must be provided separately)
        """
        if role_info.get("authenticated"):
            return f"user_{role_info.get('user_id')}"
        else:
            return "public"  # Should be replaced with session_id


# ============================================
# Global Role Detector Instance
# ============================================

role_detector = RoleDetector()
