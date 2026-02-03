"""
Configuration Management
Load settings from environment variables using Pydantic
"""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "AI Chatbot LMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # DeepSeek API
    DEEPSEEK_API_KEY: str
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_FAQ_ID: str = "faq_public_id"
    QDRANT_COLLECTION_FAQ_EN: str = "faq_public_en"
    
    # Databases
    AI_DB_PATH: str = "./data/databases/ai_chat.db"
    
    # Rate Limiting
    RATE_LIMIT_PUBLIC: int = 20
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # CORS - Parse JSON string to list
    CORS_ORIGINS: str = '["http://localhost:8080", "http://localhost:3000"]'
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string to list"""
        try:
            if self.CORS_ORIGINS.startswith('['):
                return json.loads(self.CORS_ORIGINS)
            else:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
        except:
            # Fallback - allow all in development
            if self.ENVIRONMENT == "development":
                return ["*"]
            return ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
