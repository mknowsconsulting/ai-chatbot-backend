"""
Session Manager
Manage chat sessions for public and authenticated users
"""

from typing import Optional, Dict, Any
import logging
from datetime import datetime

from app.core.database import ai_db
from app.utils.helpers import generate_session_id

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manage chat sessions
    - Create new sessions
    - Load existing sessions
    - Track session activity
    """
    
    def __init__(self):
        self.db = ai_db
    
    async def get_or_create_session(
        self,
        session_id: Optional[str],
        role_info: Dict[str, Any],
        language: str = "id",
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get existing session or create new one
        
        Args:
            session_id: Session ID (for public users)
            role_info: Role information from role detector
            language: Detected language
            user_agent: Browser user agent
            ip_address: Client IP address
            
        Returns:
            Session information
        """
        
        # For authenticated users, use user_id as session identifier
        if role_info.get("authenticated"):
            session_id = f"user_{role_info.get('user_id')}"
        else:
            # For public users, generate session_id if not provided
            if not session_id:
                session_id = generate_session_id()
        
        # Check if session exists
        existing = await self._get_session(session_id)
        
        if existing:
            # Update last activity
            await self._update_session_activity(session_id, language)
            return existing
        else:
            # Create new session
            return await self._create_session(
                session_id=session_id,
                role_info=role_info,
                language=language,
                user_agent=user_agent,
                ip_address=ip_address
            )
    
    async def _get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session from database"""
        query = "SELECT * FROM chat_sessions WHERE session_id = ?"
        return await self.db.fetch_one(query, (session_id,))
    
    async def _create_session(
        self,
        session_id: str,
        role_info: Dict[str, Any],
        language: str,
        user_agent: Optional[str],
        ip_address: Optional[str]
    ) -> Dict[str, Any]:
        """Create new session"""
        
        query = """
            INSERT INTO chat_sessions 
            (session_id, user_id, nim, user_role, language, user_agent, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        user_id = role_info.get("user_id")
        nim = role_info.get("nim")
        user_role = role_info.get("role", "public")
        
        await self.db.execute(
            query,
            (session_id, user_id, nim, user_role, language, user_agent, ip_address)
        )
        
        logger.info(f"Created new session: {session_id} (role: {user_role})")
        
        return await self._get_session(session_id)
    
    async def _update_session_activity(self, session_id: str, language: str):
        """Update session last activity"""
        query = """
            UPDATE chat_sessions 
            SET last_activity = CURRENT_TIMESTAMP,
                language = ?,
                message_count = message_count + 1
            WHERE session_id = ?
        """
        await self.db.execute(query, (language, session_id))
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> list:
        """
        Get chat history for session
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages
            
        Returns:
            List of messages (user and assistant)
        """
        
        query = """
            SELECT role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        messages = await self.db.fetch_all(query, (session_id, limit))
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        language: Optional[str] = None,
        tokens_used: int = 0,
        response_time_ms: int = 0
    ):
        """
        Save message to database
        
        Args:
            session_id: Session ID
            role: Message role (user/assistant/system)
            content: Message content
            language: Message language
            tokens_used: Tokens used (for cost tracking)
            response_time_ms: Response time in milliseconds
        """
        
        query = """
            INSERT INTO chat_messages 
            (session_id, role, content, language, tokens_used, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        await self.db.execute(
            query,
            (session_id, role, content, language, tokens_used, response_time_ms)
        )
        
        logger.debug(f"Saved {role} message to session {session_id}")


# ============================================
# Global Session Manager Instance
# ============================================

session_manager = SessionManager()
