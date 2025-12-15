"""
Database Connection Management
Handles SQLite (AI Chat) and PostgreSQL (LMS) connections
"""

import aiosqlite
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================
# SQLite Connection (AI Chat Database)
# ============================================

class AIDatabase:
    """SQLite database for AI chat history and analytics"""
    
    def __init__(self):
        self.db_path = settings.AI_DB_PATH
        self._ensure_db_directory()
        self._initialized = False
    
    def _ensure_db_directory(self):
        """Create database directory if not exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"📁 Created database directory: {db_dir}")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get async SQLite connection with dict row factory"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db
    
    async def initialize(self):
        """Initialize database with schema"""
        if self._initialized:
            logger.info("Database already initialized")
            return
        
        schema_path = "app/db/migrations/init_schema.sql"
        
        if not os.path.exists(schema_path):
            logger.error(f"❌ Schema file not found: {schema_path}")
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        logger.info("🔄 Initializing AI Chat database...")
        
        try:
            async with self.get_connection() as db:
                # Read and execute schema
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = f.read()
                
                await db.executescript(schema)
                await db.commit()
                
                # Verify tables created
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                tables = await cursor.fetchall()
                table_names = [row[0] for row in tables]
                
                logger.info(f"✅ AI Chat database initialized")
                logger.info(f"📊 Tables created: {len(table_names)}")
                logger.info(f"   {', '.join(table_names)}")
                
                self._initialized = True
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    async def execute(self, query: str, params: tuple = ()):
        """Execute a query (INSERT, UPDATE, DELETE)"""
        async with self.get_connection() as db:
            try:
                cursor = await db.execute(query, params)
                await db.commit()
                return cursor.lastrowid
            except Exception as e:
                logger.error(f"Execute error: {e}")
                raise
    
    async def fetch_one(self, query: str, params: tuple = ()):
        """Fetch one row as dict"""
        async with self.get_connection() as db:
            try:
                cursor = await db.execute(query, params)
                row = await cursor.fetchone()
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"Fetch one error: {e}")
                raise
    
    async def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows as list of dicts"""
        async with self.get_connection() as db:
            try:
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Fetch all error: {e}")
                raise
    
    async def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = await self.fetch_one(query)
        return result['count'] if result else 0


# ============================================
# PostgreSQL Connection (LMS Database)
# ============================================

class LMSDatabase:
    """PostgreSQL connection to LMS database (READ-ONLY)"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._connected = False
    
    def connect(self):
        """Initialize PostgreSQL connection"""
        
        # Check if LMS DB is configured
        if not settings.lms_database_url:
            logger.warning("⚠️  LMS Database not configured (missing credentials)")
            logger.warning("   Student data features will be disabled")
            return
        
        try:
            logger.info("🔄 Connecting to LMS Database...")
            
            # Create engine with read-only configuration
            self.engine = create_engine(
                settings.lms_database_url,
                poolclass=NullPool,
                pool_pre_ping=True,
                echo=settings.DEBUG,
                connect_args={
                    "options": "-c default_transaction_read_only=on"
                }
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            self._connected = True
            logger.info("✅ LMS Database connected (PostgreSQL - READ ONLY)")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to LMS Database: {e}")
            logger.warning("   Student data features will be disabled")
            self.engine = None
            self._connected = False
    
    def get_session(self):
        """Get database session"""
        if not self.is_connected():
            raise Exception("LMS Database not connected")
        return self.SessionLocal()
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._connected
    
    def disconnect(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("LMS Database disconnected")


# ============================================
# Global Database Instances
# ============================================

ai_db = AIDatabase()
lms_db = LMSDatabase()


# ============================================
# Initialization Function
# ============================================

async def init_databases():
    """Initialize all databases on application startup"""
    logger.info("=" * 60)
    logger.info("🔄 Initializing Databases...")
    logger.info("=" * 60)
    
    # 1. Initialize AI Chat Database (SQLite) - REQUIRED
    try:
        await ai_db.initialize()
        
        # Show initial stats
        sessions_count = await ai_db.get_table_count('chat_sessions')
        messages_count = await ai_db.get_table_count('chat_messages')
        admins_count = await ai_db.get_table_count('admin_users')
        
        logger.info(f"   📊 Current data:")
        logger.info(f"      - Chat sessions: {sessions_count}")
        logger.info(f"      - Messages: {messages_count}")
        logger.info(f"      - Admin users: {admins_count}")
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: AI Database initialization failed: {e}")
        raise
    
    # 2. Connect to LMS Database (PostgreSQL) - OPTIONAL
    try:
        lms_db.connect()
    except Exception as e:
        logger.warning(f"⚠️  LMS Database connection skipped: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ Database Initialization Complete")
    logger.info("=" * 60)


async def close_databases():
    """Close all database connections"""
    logger.info("Closing database connections...")
    lms_db.disconnect()
    logger.info("Database connections closed")


# ============================================
# FastAPI Dependencies
# ============================================

async def get_ai_db():
    """Dependency injection for AI database"""
    return ai_db


def get_lms_db():
    """Dependency injection for LMS database"""
    if not lms_db.is_connected():
        raise Exception("LMS Database not available")
    
    db = lms_db.get_session()
    try:
        yield db
    finally:
        db.close()
