"""
Chat API Endpoint - PUBLIC VERSION (No Auth Required)
Input validation and security headers only
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Optional
import time
import logging

from app.models.chat import ChatRequest, ChatResponse, ErrorResponse, FAQResult, ChatMetadata
from app.services.language_detector import language_detector
from app.services.session_manager import session_manager
from app.services.rate_limiter import rate_limiter
from app.services.rag_service import rag_service
from app.services.analytics_service import analytics_service
from app.utils.helpers import get_current_timestamp
from app.middleware.security import sanitize_input, validate_session_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/message", response_model=ChatResponse, responses={429: {"model": ErrorResponse}})
async def chat(
    request: Request,
    chat_request: ChatRequest
):
    """
    Public chat endpoint - No authentication required
    """
    
    start_time = time.time()
    
    try:
        # INPUT VALIDATION
        user_message = sanitize_input(chat_request.message)
        
        if not user_message:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Message cannot be empty",
                    "timestamp": get_current_timestamp()
                }
            )
        
        if chat_request.session_id:
            chat_request.session_id = validate_session_id(chat_request.session_id)
        
        # DETECT LANGUAGE
        language = chat_request.language or language_detector.detect_language(user_message)
        
        # GET OR CREATE SESSION
        session = await session_manager.get_or_create_session(
            session_id=chat_request.session_id,
            role_info={"role": "public"},
            language=language,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host
        )
        
        session_id = session["session_id"]
        
        # RATE LIMIT
        rate_limit_result = await rate_limiter.check_rate_limit(session_id, "public")
        
        if not rate_limit_result["allowed"]:
            logger.warning(f"Rate limit exceeded for {session_id}")
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
        
        # GET HISTORY
        history = await session_manager.get_session_history(session_id, limit=5)
        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]
        
        # GENERATE AI RESPONSE
        ai_response = await rag_service.search_and_generate(
            user_message=user_message,
            language=language,
            user_role="public",
            student_context=None,
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
        
        # SAVE MESSAGES
        response_time_ms = int((time.time() - start_time) * 1000)
        tokens_used = ai_response.get("metadata", {}).get("tokens", {}).get("total", 0)
        cost_usd = ai_response.get("metadata", {}).get("cost", {}).get("total", 0.0)
        
        await session_manager.save_message(
            session_id=session_id,
            role="user",
            content=user_message,
            language=language
        )
        
        await session_manager.save_message(
            session_id=session_id,
            role="assistant",
            content=ai_response["answer"],
            language=language,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms
        )
        
        # INCREMENT RATE LIMIT
        await rate_limiter.increment_usage(session_id, "public")
        await analytics_service.record_question(user_message, language)
        
        rate_limit_result = await rate_limiter.check_rate_limit(session_id, "public")
        
        # FORMAT RESPONSE
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
            role="public",
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
            f"Chat completed: public | {language} | "
            f"{tokens_used} tokens | {response_time_ms}ms | "
            f"Rate: {rate_limit_result['used']}/{rate_limit_result['remaining']}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {type(e).__name__}", exc_info=True)
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
        session_id = validate_session_id(session_id)
        
        if limit > 100:
            limit = 100
        
        history = await session_manager.get_session_history(session_id, limit)
        
        return {
            "success": True,
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }
        
    except HTTPException:
        raise
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
