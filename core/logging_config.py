"""
Advanced logging configuration for the Feature Store API.
Supports structured logging, different log levels per environment, and JSON formatting.
"""
import logging
import json
import sys
from typing import Dict, Any
from core.settings import settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'path'):
            log_entry['path'] = record.path
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'client_ip'):
            log_entry['client_ip'] = record.client_ip
        
        return json.dumps(log_entry)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for development environment."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Create colored level name
        colored_level = f"{color}{record.levelname}{reset}"
        
        # Format the message
        formatted = super().format(record)
        return formatted.replace(record.levelname, colored_level)

def setup_logging():
    """Setup logging configuration based on environment."""
    
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Choose formatter based on environment
    if settings.is_development():
        # Development: Colored, human-readable format
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Production/Staging: JSON format for log aggregation
        formatter = JSONFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_loggers()
    
    return root_logger

def configure_loggers():
    """Configure specific loggers for different components."""
    
    # FastAPI logger
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(logging.INFO)
    
    # Uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.INFO)
    
    # Our application logger
    app_logger = logging.getLogger("feature_store")
    app_logger.setLevel(logging.DEBUG if settings.is_development() else logging.INFO)
    
    # Boto3 logger (AWS SDK)
    boto3_logger = logging.getLogger("boto3")
    boto3_logger.setLevel(logging.WARNING)
    
    # Botocore logger (AWS SDK)
    botocore_logger = logging.getLogger("botocore")
    botocore_logger.setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration."""
    return logging.getLogger(f"feature_store.{name}")

# Setup logging on import
setup_logging()
