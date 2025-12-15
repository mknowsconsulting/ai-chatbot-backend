"""
Chat API Endpoint
Main endpoint for chatbot interactions
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from typing import Optional
import time
import logging

from app.models.chat import ChatRequest, ChatResponse, ErrorResponse, FAQResult, ChatMetadata
from app.services.role_detector import role_detector
from app.services.language_detector import language_detector
from app.services.session_manager import session_manager
from app.services.rate_limiter import rate_limiter
from app.services.rag_service import rag_service
from app.services.student_data_service_mock import MockStudentDataService
from app.services.analytics_service import analytics_service
from app.utils.helpers import get_current_timestamp

logger = logging.getLogger(__name__)

router = APIRouter()

# Use mock student service for now
student_service = MockStudentDataService()


@router.post("/message", response_model=ChatResponse, responses={429: {"model": ErrorResponse}})
async def chat(
    request: Request,
    chat_request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Main chat endpoint (renamed from /chat to /message to avoid adblockers)
    
    Handles all user interactions with chatbot
    """
    
    start_time = time.time()
    
    try:
        # ... (rest of the code stays the same)
        # ============================================
        # 1. DETECT USER ROLE
        # ============================================
        role_info = role_detector.detect_from_request(request)
        user_role = role_info.get("role", "public")
        
        logger.info(f"Chat request from {user_role}: {chat_request.message[:50]}...")
        
        # ============================================
        # 2. DETECT LANGUAGE
        # ============================================
        if chat_request.language:
            language = chat_request.language
        else:
            language = language_detector.detect_language(chat_request.message)
        
        logger.debug(f"Detected language: {language}")
        
        # ============================================
        # 3. GET OR CREATE SESSION
        # ============================================
        session = await session_manager.get_or_create_session(
            session_id=chat_request.session_id,
            role_info=role_info,
            language=language,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host
        )
        
        session_id = session["session_id"]
        
        # ============================================
        # 4. CHECK RATE LIMIT
        # ============================================
        identifier = session_id if user_role == "public" else f"user_{role_info.get('user_id')}"
        
        rate_limit_result = await rate_limiter.check_rate_limit(identifier, user_role)
        
        if not rate_limit_result["allowed"]:
            logger.warning(f"Rate limit exceeded for {identifier}")
            raise HTTPException(
                status_code=429,
                detail={
                    "success": False,
                    "error": "Rate limit exceeded. Please try again tomorrow.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "rate_limit": rate_limit_result,
                    "timestamp": get_current_timestamp()
                }
            )
        
        # ============================================
        # 5. GET CONVERSATION HISTORY
        # ============================================
        history = await session_manager.get_session_history(session_id, limit=5)
        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]
        
        # ============================================
        # 6. PREPARE STUDENT CONTEXT (if student)
        # ============================================
        student_context = None
        if user_role == "student" and role_info.get("nim"):
            nim = role_info["nim"]
            student_data = student_service.format_student_context_for_ai(nim)
            student_context = {
                "name": role_info.get("name", ""),
                "nim": nim,
                "data": student_data
            }
            logger.debug(f"Loaded student context for NIM: {nim}")
        
        # ============================================
        # 7. GENERATE AI RESPONSE (RAG)
        # ============================================
        ai_response = await rag_service.search_and_generate(
            user_message=chat_request.message,
            language=language,
            user_role=user_role,
            student_context=student_context,
            conversation_history=conversation_history
        )
        
        if not ai_response.get("success"):
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to generate response",
                    "error_code": "AI_GENERATION_FAILED",
                    "timestamp": get_current_timestamp()
                }
            )
        
        # ============================================
        # 8. SAVE MESSAGES TO DATABASE
        # ============================================
        response_time_ms = int((time.time() - start_time) * 1000)
        tokens_used = ai_response.get("metadata", {}).get("tokens", {}).get("total", 0)
        cost_usd = ai_response.get("metadata", {}).get("cost", {}).get("total", 0.0)
        
        # Save user message
        await session_manager.save_message(
            session_id=session_id,
            role="user",
            content=chat_request.message,
            language=language
        )
        
        # Save assistant response
        await session_manager.save_message(
            session_id=session_id,
            role="assistant",
            content=ai_response["answer"],
            language=language,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms
        )
        
        # ============================================
        # 9. INCREMENT RATE LIMIT & ANALYTICS
        # ============================================
        await rate_limiter.increment_usage(identifier, user_role)
        
        # Record question for analytics
        await analytics_service.record_question(chat_request.message, language)
        
        # Update rate limit result after increment
        rate_limit_result = await rate_limiter.check_rate_limit(identifier, user_role)
        
        # ============================================
        # 10. FORMAT RESPONSE
        # ============================================
        faq_results = [
            FAQResult(
                question=faq["question"],
                answer=faq["answer"],
                score=faq["score"],
                category=faq.get("category")
            )
            for faq in ai_response.get("faq_results", [])
        ]
        
        metadata = ChatMetadata(
            session_id=session_id,
            role=user_role,
            language=language,
            faq_count=ai_response.get("faq_count", 0),
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            rate_limit={
                "limit": rate_limit_result["limit"],
                "used": rate_limit_result["used"],
                "remaining": rate_limit_result["remaining"]
            }
        )
        
        response = ChatResponse(
            success=True,
            reply=ai_response["answer"],
            metadata=metadata,
            faq_results=faq_results if faq_results else None,
            timestamp=get_current_timestamp()
        )
        
        logger.info(
            f"Chat completed: {user_role} | {language} | "
            f"{tokens_used} tokens | {response_time_ms}ms | "
            f"Rate: {rate_limit_result['used']}/{rate_limit_result['limit']}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "timestamp": get_current_timestamp()
            }
        )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 20
):
    """Get chat history for a session"""
    
    try:
        history = await session_manager.get_session_history(session_id, limit)
        
        return {
            "success": True,
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to fetch history",
                "timestamp": get_current_timestamp()
            }
        )
