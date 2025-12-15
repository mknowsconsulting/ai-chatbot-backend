"""
LLM Service - DeepSeek API Integration
Handles all interactions with DeepSeek language model
"""

from typing import List, Dict, Any, Optional
import httpx
import logging
import time
from datetime import datetime

from app.core.config import settings
from app.utils.helpers import calculate_cost

logger = logging.getLogger(__name__)


class DeepSeekService:
    """
    DeepSeek API Service
    Handles chat completions with DeepSeek language model
    """
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        self.model = settings.DEEPSEEK_MODEL
        self.timeout = 30.0  # 30 seconds timeout
        
        # Token costs (DeepSeek pricing)
        # Input: $0.14 per 1M tokens
        # Output: $0.28 per 1M tokens
        self.cost_per_1m_input_tokens = 0.14
        self.cost_per_1m_output_tokens = 0.28
    
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Create chat completion with DeepSeek API
        
        Args:
            messages: List of message objects [{"role": "user", "content": "..."}]
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens in response
            stream: Whether to stream response
            
        Returns:
            Dictionary with response and metadata
            
        Example:
            response = await llm_service.create_chat_completion([
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello!"}
            ])
        """
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                
                # Prepare request
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream
                }
                
                # Make API request
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                # Check response status
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                
                # Calculate metrics
                end_time = time.time()
                response_time = end_time - start_time
                
                # Extract usage data
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                
                # Calculate cost
                input_cost = calculate_cost(prompt_tokens, self.cost_per_1m_input_tokens)
                output_cost = calculate_cost(completion_tokens, self.cost_per_1m_output_tokens)
                total_cost = input_cost + output_cost
                
                # Extract response content
                content = data["choices"][0]["message"]["content"]
                
                # Log request
                logger.info(
                    f"DeepSeek API | Tokens: {total_tokens} "
                    f"(in: {prompt_tokens}, out: {completion_tokens}) | "
                    f"Cost: ${total_cost:.4f} | Time: {response_time:.2f}s"
                )
                
                return {
                    "success": True,
                    "content": content,
                    "metadata": {
                        "model": self.model,
                        "tokens": {
                            "prompt": prompt_tokens,
                            "completion": completion_tokens,
                            "total": total_tokens
                        },
                        "cost": {
                            "input": input_cost,
                            "output": output_cost,
                            "total": total_cost
                        },
                        "response_time": response_time,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"API error: {e.response.status_code}",
                "content": None
            }
            
        except httpx.TimeoutException:
            logger.error("DeepSeek API timeout")
            return {
                "success": False,
                "error": "Request timeout",
                "content": None
            }
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate AI response with context and history
        
        Args:
            system_prompt: System instruction for AI
            user_message: User's current message
            context: Additional context (FAQ, student data, etc.)
            conversation_history: Previous messages
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            Response dictionary
            
        Example:
            response = await llm_service.generate_response(
                system_prompt="You are a helpful assistant for students",
                user_message="What is my GPA?",
                context="Student GPA: 3.5"
            )
        """
        
        # Build messages array
        messages = []
        
        # 1. System prompt
        full_system_prompt = system_prompt
        if context:
            full_system_prompt += f"\n\nContext:\n{context}"
        
        messages.append({
            "role": "system",
            "content": full_system_prompt
        })
        
        # 2. Conversation history (last 5 messages for context)
        if conversation_history:
            messages.extend(conversation_history[-5:])
        
        # 3. Current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Generate completion
        return await self.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def test_connection(self) -> bool:
        """
        Test DeepSeek API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = await self.create_chat_completion(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return response.get("success", False)
            
        except Exception as e:
            logger.error(f"DeepSeek connection test failed: {e}")
            return False


# ============================================
# PROMPT TEMPLATES
# ============================================

class PromptTemplates:
    """
    Pre-defined prompt templates for different user roles and scenarios
    """
    
    @staticmethod
    def get_public_system_prompt(language: str = "id") -> str:
        """System prompt for public users"""
        if language == "id":
            return """Anda adalah asisten virtual untuk Kampus Gratis Indonesia.

Tugas Anda:
- Menjawab pertanyaan umum tentang kampus dari FAQ yang diberikan
- Memberikan informasi yang akurat dan profesional
- Jika tidak ada informasi di FAQ, katakan dengan sopan bahwa Anda tidak memiliki informasi tersebut
- Jangan gunakan emoji
- Gunakan bahasa Indonesia yang baik dan benar

Gaya komunikasi:
- Profesional namun ramah
- Singkat dan jelas
- Informatif"""
        else:  # English
            return """You are a virtual assistant for Kampus Gratis Indonesia.

Your tasks:
- Answer general questions about the campus from provided FAQ
- Provide accurate and professional information
- If information is not in FAQ, politely say you don't have that information
- Don't use emojis
- Use proper English

Communication style:
- Professional but friendly
- Brief and clear
- Informative"""
    
    @staticmethod
    def get_student_system_prompt(
        student_name: str,
        nim: str,
        language: str = "id"
    ) -> str:
        """System prompt for student users"""
        if language == "id":
            return f"""Anda adalah asisten pribadi untuk mahasiswa {student_name} (NIM: {nim}) di Kampus Gratis Indonesia.

Tugas Anda:
- Membantu mahasiswa dengan informasi akademik pribadi mereka
- Menjawab pertanyaan tentang nilai, jadwal, tugas, dan kehadiran
- Memberikan motivasi dan dukungan
- Jika data tidak tersedia, katakan dengan jelas

Data mahasiswa akan diberikan dalam context.

Gaya komunikasi:
- Personal dan supportive
- Panggil mahasiswa dengan nama
- Berikan respon yang membantu dan memotivasi
- Jangan gunakan emoji berlebihan (maksimal 1-2 per response)"""
        else:
            return f"""You are a personal assistant for student {student_name} (NIM: {nim}) at Kampus Gratis Indonesia.

Your tasks:
- Help students with their personal academic information
- Answer questions about grades, schedules, assignments, and attendance
- Provide motivation and support
- If data is not available, state it clearly

Student data will be provided in context.

Communication style:
- Personal and supportive
- Address student by name
- Provide helpful and motivating responses
- Don't overuse emojis (max 1-2 per response)"""
    
    @staticmethod
    def get_admin_system_prompt(language: str = "id") -> str:
        """System prompt for admin users"""
        if language == "id":
            return """Anda adalah asisten untuk administrator Kampus Gratis Indonesia.

Tugas Anda:
- Membantu admin dengan analisis dan insights
- Memberikan informasi tentang sistem chatbot
- Menjawab pertanyaan teknis
- Memberikan rekomendasi berdasarkan data

Gaya komunikasi:
- Profesional dan teknis
- Data-driven
- Memberikan insights dan rekomendasi"""
        else:
            return """You are an assistant for administrators of Kampus Gratis Indonesia.

Your tasks:
- Help admins with analysis and insights
- Provide information about chatbot system
- Answer technical questions
- Give recommendations based on data

Communication style:
- Professional and technical
- Data-driven
- Provide insights and recommendations"""


# ============================================
# Global LLM Service Instance
# ============================================

llm_service = DeepSeekService()
prompt_templates = PromptTemplates()
