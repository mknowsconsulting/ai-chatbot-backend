"""
Rate Limiting Service
Control request limits based on user role
- Public: 20 requests/day
- Student: 100 requests/day
- Admin: Unlimited
"""

from typing import Dict, Any, Optional
from datetime import date, datetime
import logging

from app.core.config import settings
from app.core.database import ai_db
from app.utils.helpers import get_current_date

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiting service based on user role
    """
    
    def __init__(self):
        self.db = ai_db
        
        # Rate limits from config
        self.limits = {
            "public": settings.RATE_LIMIT_PUBLIC,
            "student": settings.RATE_LIMIT_STUDENT,
            "admin": settings.RATE_LIMIT_ADMIN
        }
    
    async def check_rate_limit(
        self,
        identifier: str,
        user_role: str = "public"
    ) -> Dict[str, Any]:
        """
        Check if user has exceeded rate limit
        
        Args:
            identifier: Unique identifier (session_id for public, user_id for authenticated)
            user_role: User role (public, student, admin)
            
        Returns:
            Dictionary with limit info:
            {
                "allowed": True/False,
                "limit": 20,
                "used": 5,
                "remaining": 15,
                "reset_at": "2024-12-16T00:00:00Z"
            }
        """
        
        # Admin has unlimited access
        if user_role == "admin":
            return {
                "allowed": True,
                "limit": self.limits["admin"],
                "used": 0,
                "remaining": self.limits["admin"],
                "reset_at": None
            }
        
        # Get limit for role
        limit = self.limits.get(user_role, self.limits["public"])
        
        # Get current usage
        today = get_current_date()
        usage = await self._get_usage(identifier, today)
        
        # Check if exceeded
        allowed = usage < limit
        remaining = max(0, limit - usage)
        
        # Calculate reset time (midnight tomorrow)
        reset_at = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        reset_at = reset_at.replace(day=reset_at.day + 1)
        
        return {
            "allowed": allowed,
            "limit": limit,
            "used": usage,
            "remaining": remaining,
            "reset_at": reset_at.isoformat()
        }
    
    async def increment_usage(
        self,
        identifier: str,
        user_role: str = "public"
    ):
        """
        Increment usage count for user
        
        Args:
            identifier: Unique identifier
            user_role: User role
        """
        
        today = get_current_date()
        
        # Check if record exists
        query_check = """
            SELECT id, request_count 
            FROM rate_limits 
            WHERE identifier = ? AND date = ?
        """
        
        existing = await self.db.fetch_one(query_check, (identifier, today))
        
        if existing:
            # Update existing record
            query_update = """
                UPDATE rate_limits 
                SET request_count = request_count + 1,
                    last_request = CURRENT_TIMESTAMP
                WHERE identifier = ? AND date = ?
            """
            await self.db.execute(query_update, (identifier, today))
        else:
            # Create new record
            query_insert = """
                INSERT INTO rate_limits (identifier, user_role, date, request_count, last_request)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            """
            await self.db.execute(query_insert, (identifier, user_role, today))
        
        logger.debug(f"Incremented usage for {identifier} ({user_role})")
    
    async def _get_usage(self, identifier: str, date_str: str) -> int:
        """
        Get current usage count
        
        Args:
            identifier: Unique identifier
            date_str: Date string (YYYY-MM-DD)
            
        Returns:
            Current request count
        """
        
        query = """
            SELECT request_count 
            FROM rate_limits 
            WHERE identifier = ? AND date = ?
        """
        
        result = await self.db.fetch_one(query, (identifier, date_str))
        
        if result:
            return result["request_count"]
        return 0
    
    async def reset_usage(self, identifier: str):
        """
        Reset usage for identifier (admin function)
        
        Args:
            identifier: Unique identifier
        """
        
        today = get_current_date()
        
        query = """
            DELETE FROM rate_limits 
            WHERE identifier = ? AND date = ?
        """
        
        await self.db.execute(query, (identifier, today))
        logger.info(f"Reset usage for {identifier}")
    
    async def get_usage_stats(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics (for analytics)
        
        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            
        Returns:
            Usage statistics
        """
        
        # Default to today if not specified
        if not date_from:
            date_from = get_current_date()
        if not date_to:
            date_to = get_current_date()
        
        query = """
            SELECT 
                user_role,
                COUNT(DISTINCT identifier) as unique_users,
                SUM(request_count) as total_requests,
                AVG(request_count) as avg_requests_per_user
            FROM rate_limits
            WHERE date BETWEEN ? AND ?
            GROUP BY user_role
        """
        
        results = await self.db.fetch_all(query, (date_from, date_to))
        
        stats = {
            "date_from": date_from,
            "date_to": date_to,
            "by_role": {}
        }
        
        for row in results:
            stats["by_role"][row["user_role"]] = {
                "unique_users": row["unique_users"],
                "total_requests": row["total_requests"],
                "avg_requests_per_user": round(row["avg_requests_per_user"], 2)
            }
        
        return stats
    
    async def cleanup_old_records(self, days_to_keep: int = 30):
        """
        Clean up old rate limit records
        
        Args:
            days_to_keep: Number of days to keep records
        """
        
        query = """
            DELETE FROM rate_limits 
            WHERE date < date('now', '-' || ? || ' days')
        """
        
        await self.db.execute(query, (days_to_keep,))
        logger.info(f"Cleaned up rate limit records older than {days_to_keep} days")


# ============================================
# Global Rate Limiter Instance
# ============================================

rate_limiter = RateLimiter()
