"""
Authentication API
Student login endpoint
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.core.security import create_student_token, verify_password
from app.services.student_data_service_mock import MockStudentDataService
from app.utils.helpers import get_current_timestamp

logger = logging.getLogger(__name__)

router = APIRouter()

# Use mock service for now
student_service = MockStudentDataService()


class LoginRequest(BaseModel):
    """Student login request"""
    nim: str
    password: str


class LoginResponse(BaseModel):
    """Login response"""
    success: bool
    token: str
    user: dict
    expires_at: str


@router.post("/student-login", response_model=LoginResponse)
async def student_login(request: LoginRequest):
    """
    Student login endpoint
    
    Returns JWT token for authenticated student
    """
    
    try:
        # Get student by NIM
        student = student_service.get_student_by_nim(request.nim)
        
        if not student:
            logger.warning(f"Login failed: NIM {request.nim} not found")
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": "Invalid NIM or password",
                    "timestamp": get_current_timestamp()
                }
            )
        
        # Verify password (in real implementation)
        # For mock, we accept any password
        # if not verify_password(request.password, student_password_hash):
        #     raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create JWT token
        token = create_student_token(
            user_id=student["id"],
            nim=student["nim"],
            name=student["full_name"],
            jurusan=student["jurusan"],
            semester=student["semester"]
        )
        
        # Calculate expiry (24 hours from now)
        from datetime import datetime, timedelta
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
        
        logger.info(f"Student login successful: {student['nim']}")
        
        return LoginResponse(
            success=True,
            token=token,
            user={
                "user_id": student["id"],
                "nim": student["nim"],
                "name": student["full_name"],
                "jurusan": student["jurusan"],
                "semester": student["semester"],
                "role": "student"
            },
            expires_at=expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Login failed",
                "timestamp": get_current_timestamp()
            }
        )
