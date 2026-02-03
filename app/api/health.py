"""
Healthcheck endpoint untuk Railway
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"status": "ok", "message": "AI Chatbot API is running"}

@router.get("/health")
async def health():
    return {"status": "healthy"}
