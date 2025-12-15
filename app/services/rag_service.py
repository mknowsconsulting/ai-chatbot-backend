"""
RAG Service (Retrieval-Augmented Generation)
Combines FAQ search (Qdrant) with LLM generation (DeepSeek)
"""

from typing import List, Dict, Any, Optional
import logging

from app.services.qdrant_service import qdrant_service
from app.services.llm_service import llm_service, prompt_templates
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) Service
    Search FAQs and generate contextual responses
    """
    
    def __init__(self):
        self.qdrant = qdrant_service
        self.llm = llm_service
        self.prompts = prompt_templates
    
    async def search_and_generate(
        self,
        user_message: str,
        language: str = "id",
        user_role: str = "public",
        limit: int = 3,
        score_threshold: float = 0.6,
        student_context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Search FAQs and generate AI response
        
        Args:
            user_message: User's question
            language: Language (id/en)
            user_role: User role (public/student/admin)
            limit: Max FAQ results
            score_threshold: Minimum similarity score
            student_context: Student data (for student role)
            conversation_history: Previous messages
            
        Returns:
            Response with FAQ results and AI answer
        """
        
        # 1. Determine collection
        collection_name = (
            settings.QDRANT_COLLECTION_FAQ_ID if language == "id"
            else settings.QDRANT_COLLECTION_FAQ_EN
        )
        
        # 2. Search FAQs
        faq_results = self.qdrant.search_faq(
            collection_name=collection_name,
            query=user_message,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # 3. Build context from FAQs
        faq_context = self._build_faq_context(faq_results)
        
        # 4. Get system prompt based on role
        if user_role == "student" and student_context:
            system_prompt = self.prompts.get_student_system_prompt(
                student_name=student_context.get("name", ""),
                nim=student_context.get("nim", ""),
                language=language
            )
            # Combine FAQ context with student data
            full_context = f"{faq_context}\n\n{student_context.get('data', '')}"
        elif user_role == "admin":
            system_prompt = self.prompts.get_admin_system_prompt(language)
            full_context = faq_context
        else:  # public
            system_prompt = self.prompts.get_public_system_prompt(language)
            full_context = faq_context
        
        # 5. Generate AI response
        ai_response = await self.llm.generate_response(
            system_prompt=system_prompt,
            user_message=user_message,
            context=full_context if full_context.strip() else None,
            conversation_history=conversation_history,
            temperature=0.7,
            max_tokens=800
        )
        
        # 6. Return combined result
        return {
            "success": ai_response.get("success", False),
            "answer": ai_response.get("content", ""),
            "faq_results": faq_results,
            "faq_count": len(faq_results),
            "metadata": ai_response.get("metadata", {})
        }
    
    def _build_faq_context(self, faq_results: List[Dict[str, Any]]) -> str:
        """
        Build context string from FAQ results
        
        Args:
            faq_results: List of FAQ search results
            
        Returns:
            Formatted context string
        """
        if not faq_results:
            return ""
        
        context_parts = []
        for i, faq in enumerate(faq_results, 1):
            context_parts.append(
                f"FAQ {i} (relevance: {faq['score']:.2f}):\n"
                f"Q: {faq['question']}\n"
                f"A: {faq['answer']}\n"
            )
        
        return "\n".join(context_parts)
    
    async def answer_without_rag(
        self,
        user_message: str,
        language: str = "id",
        user_role: str = "public",
        student_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate answer without FAQ search (for questions that need direct response)
        
        Args:
            user_message: User's message
            language: Language
            user_role: User role
            student_context: Student data
            conversation_history: Previous messages
            
        Returns:
            AI response
        """
        
        # Get system prompt
        if user_role == "student" and student_context:
            system_prompt = self.prompts.get_student_system_prompt(
                student_name=student_context.get("name", ""),
                nim=student_context.get("nim", ""),
                language=language
            )
            context = student_context.get("data")
        elif user_role == "admin":
            system_prompt = self.prompts.get_admin_system_prompt(language)
            context = None
        else:
            system_prompt = self.prompts.get_public_system_prompt(language)
            context = None
        
        # Generate response
        ai_response = await self.llm.generate_response(
            system_prompt=system_prompt,
            user_message=user_message,
            context=context,
            conversation_history=conversation_history,
            temperature=0.7,
            max_tokens=800
        )
        
        return {
            "success": ai_response.get("success", False),
            "answer": ai_response.get("content", ""),
            "faq_results": [],
            "faq_count": 0,
            "metadata": ai_response.get("metadata", {})
        }


# ============================================
# Global RAG Service Instance
# ============================================

rag_service = RAGService()
