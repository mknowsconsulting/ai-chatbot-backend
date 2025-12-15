"""
Analytics Service
Track and analyze chatbot usage, performance, and costs
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import logging

from app.core.database import ai_db
from app.utils.helpers import get_current_date

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analytics and reporting service
    Track usage, performance, costs
    """
    
    def __init__(self):
        self.db = ai_db
    
    async def log_chat_interaction(
        self,
        session_id: str,
        user_role: str,
        language: str,
        tokens_used: int,
        cost_usd: float,
        response_time_ms: int
    ):
        """
        Log chat interaction for analytics
        
        Args:
            session_id: Session ID
            user_role: User role
            language: Language used
            tokens_used: Total tokens
            cost_usd: API cost
            response_time_ms: Response time
        """
        
        # This would typically be aggregated and stored in chat_analytics table
        # For now, we track it through chat_messages table which already has this data
        logger.debug(
            f"Chat interaction: {user_role} | {language} | "
            f"{tokens_used} tokens | ${cost_usd:.6f} | {response_time_ms}ms"
        )
    
    async def get_daily_stats(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get daily statistics
        
        Args:
            date_str: Date (YYYY-MM-DD), default today
            
        Returns:
            Daily statistics
        """
        
        if not date_str:
            date_str = get_current_date()
        
        # Get sessions created today
        query_sessions = """
            SELECT 
                user_role,
                language,
                COUNT(*) as count
            FROM chat_sessions
            WHERE DATE(created_at) = ?
            GROUP BY user_role, language
        """
        
        sessions = await self.db.fetch_all(query_sessions, (date_str,))
        
        # Get messages sent today
        query_messages = """
            SELECT 
                COUNT(*) as total_messages,
                SUM(tokens_used) as total_tokens,
                AVG(response_time_ms) as avg_response_time
            FROM chat_messages
            WHERE DATE(created_at) = ?
        """
        
        messages = await self.db.fetch_one(query_messages, (date_str,))
        
        # Calculate cost (DeepSeek pricing)
        total_tokens = messages.get("total_tokens", 0) or 0
        estimated_cost = (total_tokens / 1_000_000) * 0.14  # $0.14 per 1M tokens
        
        return {
            "date": date_str,
            "sessions": {
                "total": sum(s["count"] for s in sessions),
                "by_role": {s["user_role"]: s["count"] for s in sessions}
            },
            "messages": {
                "total": messages.get("total_messages", 0),
                "total_tokens": total_tokens,
                "avg_response_time_ms": messages.get("avg_response_time", 0)
            },
            "cost": {
                "estimated_usd": round(estimated_cost, 4)
            }
        }
    
    async def get_popular_questions(
        self,
        limit: int = 10,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most popular questions
        
        Args:
            limit: Number of results
            language: Filter by language
            
        Returns:
            List of popular questions
        """
        
        query = """
            SELECT 
                question,
                ask_count,
                language,
                last_asked
            FROM popular_questions
        """
        
        if language:
            query += " WHERE language = ?"
            params = (language, limit)
        else:
            params = (limit,)
        
        query += " ORDER BY ask_count DESC LIMIT ?"
        
        results = await self.db.fetch_all(query, params)
        
        return [dict(r) for r in results]
    
    async def record_question(self, question: str, language: str):
        """
        Record question for popularity tracking
        
        Args:
            question: User's question
            language: Question language
        """
        
        # Normalize question
        normalized = question.lower().strip()
        
        # Check if exists
        query_check = """
            SELECT id, ask_count 
            FROM popular_questions 
            WHERE normalized_question = ? AND language = ?
        """
        
        existing = await self.db.fetch_one(
            query_check,
            (normalized, language)
        )
        
        if existing:
            # Increment count
            query_update = """
                UPDATE popular_questions 
                SET ask_count = ask_count + 1,
                    last_asked = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            await self.db.execute(query_update, (existing["id"],))
        else:
            # Create new record
            query_insert = """
                INSERT INTO popular_questions 
                (question, normalized_question, language, ask_count, last_asked)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            """
            await self.db.execute(
                query_insert,
                (question, normalized, language)
            )
    
    async def get_usage_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get usage summary for last N days
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Usage summary
        """
        
        date_from = (date.today() - timedelta(days=days)).isoformat()
        date_to = get_current_date()
        
        # Get session counts
        query_sessions = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as sessions
            FROM chat_sessions
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        sessions = await self.db.fetch_all(query_sessions, (date_from, date_to))
        
        # Get message counts
        query_messages = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as messages,
                SUM(tokens_used) as tokens
            FROM chat_messages
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        messages = await self.db.fetch_all(query_messages, (date_from, date_to))
        
        # Combine data
        daily_data = {}
        
        for s in sessions:
            daily_data[s["date"]] = {
                "sessions": s["sessions"],
                "messages": 0,
                "tokens": 0
            }
        
        for m in messages:
            if m["date"] in daily_data:
                daily_data[m["date"]]["messages"] = m["messages"]
                daily_data[m["date"]]["tokens"] = m["tokens"] or 0
            else:
                daily_data[m["date"]] = {
                    "sessions": 0,
                    "messages": m["messages"],
                    "tokens": m["tokens"] or 0
                }
        
        # Calculate totals
        total_sessions = sum(d["sessions"] for d in daily_data.values())
        total_messages = sum(d["messages"] for d in daily_data.values())
        total_tokens = sum(d["tokens"] for d in daily_data.values())
        total_cost = (total_tokens / 1_000_000) * 0.14
        
        return {
            "period": {
                "from": date_from,
                "to": date_to,
                "days": days
            },
            "totals": {
                "sessions": total_sessions,
                "messages": total_messages,
                "tokens": total_tokens,
                "cost_usd": round(total_cost, 4)
            },
            "daily": daily_data
        }


# ============================================
# Global Analytics Service Instance
# ============================================

analytics_service = AnalyticsService()
