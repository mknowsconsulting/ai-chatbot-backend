"""
Logging Utility
Configure and manage application logging
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

from app.core.config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with consistent configuration
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # File handler (if log file is configured)
    if settings.LOG_FILE:
        # Ensure log directory exists
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_api_request(logger: logging.Logger, method: str, endpoint: str, user_role: str = "unknown"):
    """
    Log API request
    
    Args:
        logger: Logger instance
        method: HTTP method
        endpoint: API endpoint
        user_role: User role making request
    """
    logger.info(f"API Request: {method} {endpoint} | Role: {user_role}")


def log_database_query(logger: logging.Logger, query: str, execution_time: float):
    """
    Log database query
    
    Args:
        logger: Logger instance
        query: SQL query (first 100 chars)
        execution_time: Query execution time in seconds
    """
    query_preview = query[:100] + "..." if len(query) > 100 else query
    logger.debug(f"DB Query ({execution_time:.3f}s): {query_preview}")


def log_error(logger: logging.Logger, error: Exception, context: str = ""):
    """
    Log error with context
    
    Args:
        logger: Logger instance
        error: Exception object
        context: Additional context
    """
    logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}")


def log_ai_request(
    logger: logging.Logger,
    prompt_tokens: int,
    completion_tokens: int,
    cost: float,
    response_time: float
):
    """
    Log AI API request
    
    Args:
        logger: Logger instance
        prompt_tokens: Tokens in prompt
        completion_tokens: Tokens in completion
        cost: Request cost in USD
        response_time: Response time in seconds
    """
    total_tokens = prompt_tokens + completion_tokens
    logger.info(
        f"AI Request | Tokens: {total_tokens} "
        f"(prompt: {prompt_tokens}, completion: {completion_tokens}) | "
        f"Cost: ${cost:.4f} | Time: {response_time:.2f}s"
    )
