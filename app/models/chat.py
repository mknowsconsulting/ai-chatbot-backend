"""
Pydantic Models for Chat API
Request and Response models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User's message", min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="Session ID for public users")
    language: Optional[str] = Field(None, description="Preferred language (id/en)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Berapa biaya kuliah?",
                "session_id": "sess_abc123",
                "language": "id"
            }
        }


class FAQResult(BaseModel):
    """FAQ search result"""
    question: str
    answer: str
    score: float
    category: Optional[str] = None


class ChatMetadata(BaseModel):
    """Chat response metadata"""
    session_id: str
    role: str
    language: str
    faq_count: int
    tokens_used: int
    cost_usd: float
    response_time_ms: int
    rate_limit: Dict[str, Any]


class ChatResponse(BaseModel):
    """Chat response model"""
    success: bool
    reply: str
    metadata: ChatMetadata
    faq_results: Optional[List[FAQResult]] = None
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "reply": "Kuliah di Kampus Gratis Indonesia sepenuhnya GRATIS...",
                "metadata": {
                    "session_id": "sess_abc123",
                    "role": "public",
                    "language": "id",
                    "faq_count": 3,
                    "tokens_used": 150,
                    "cost_usd": 0.000021,
                    "response_time_ms": 1250,
                    "rate_limit": {
                        "limit": 20,
                        "used": 5,
                        "remaining": 15
                    }
                },
                "faq_results": [
                    {
                        "question": "Berapa biaya kuliah?",
                        "answer": "Kuliah gratis...",
                        "score": 0.95,
                        "category": "biaya"
                    }
                ],
                "timestamp": "2024-12-15T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Rate limit exceeded",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "timestamp": "2024-12-15T10:30:00Z"
            }
        }
