"""
Mock LLM Service - For Testing Without API Key
Use this when DeepSeek API key is not available
"""

from typing import List, Dict, Any, Optional
import logging
import time
import random

logger = logging.getLogger(__name__)


class MockDeepSeekService:
    """Mock DeepSeek service for testing"""
    
    def __init__(self):
        self.model = "deepseek-mock"
    
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Mock chat completion"""
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Get last user message
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        # Generate mock response based on keywords
        if "biaya" in user_message.lower() or "gratis" in user_message.lower():
            content = "Kuliah di Kampus Gratis Indonesia sepenuhnya GRATIS. Tidak ada biaya pendaftaran, SPP, praktikum, atau biaya tersembunyi apapun. Semua biaya pendidikan ditanggung penuh oleh donatur dan mitra yang peduli pendidikan."
        elif "nilai" in user_message.lower() or "uts" in user_message.lower():
            content = "Halo! Berikut nilai UTS Anda semester 3:\n\n• Algoritma: 85 (A) - Excellent!\n• Database: 78 (B+) - Good job!\n• Kalkulus: 90 (A) - Outstanding!\n\nRata-rata nilai Anda: 84.3 (A-). Pertahankan performa bagus ini untuk UAS!"
        elif "jurusan" in user_message.lower():
            content = "Kampus Gratis Indonesia menyediakan 5 jurusan unggulan:\n\n1. Teknik Informatika\n2. Sistem Informasi\n3. Manajemen Bisnis\n4. Akuntansi\n5. Desain Grafis\n\nSemua jurusan terakreditasi dan diajar oleh dosen berpengalaman."
        else:
            content = f"Ini adalah mock response untuk: {user_message}\n\n[MOCK MODE: DeepSeek API not configured]"
        
        # Mock usage data
        prompt_tokens = len(user_message.split()) * 2
        completion_tokens = len(content.split()) * 2
        total_tokens = prompt_tokens + completion_tokens
        
        return {
            "success": True,
            "content": content,
            "metadata": {
                "model": "deepseek-mock",
                "tokens": {
                    "prompt": prompt_tokens,
                    "completion": completion_tokens,
                    "total": total_tokens
                },
                "cost": {
                    "input": 0.0,
                    "output": 0.0,
                    "total": 0.0
                },
                "response_time": random.uniform(0.5, 1.5),
                "timestamp": datetime.utcnow().isoformat()
            }
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
        """Mock generate response"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        return await self.create_chat_completion(messages)
    
    async def test_connection(self) -> bool:
        """Mock connection test - always returns True"""
        logger.info("Using MOCK DeepSeek service (no API key required)")
        return True


import asyncio
from datetime import datetime

# You can switch between real and mock service
# mock_llm_service = MockDeepSeekService()
