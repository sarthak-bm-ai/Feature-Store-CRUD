"""
CORS (Cross-Origin Resource Sharing) middleware for FastAPI.
Allows browsers to call APIs from different domains.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.settings import settings
from core.logging_config import get_logger

# Configure logger
logger = get_logger("cors_middleware")

def setup_cors_middleware(app: FastAPI) -> FastAPI:
    """
    Setup CORS middleware for the FastAPI app.
    Allows cross-origin requests from browsers.
    """
    
    # Define allowed origins based on environment
    if settings.is_development():
        # Development: Allow all origins for local development
        allowed_origins = ["*"]
        logger.info("CORS: Development mode - allowing all origins")
    elif settings.is_staging():
        # Staging: Allow specific staging domains
        allowed_origins = [
            "https://staging.example.com",
            "https://staging-api.example.com",
            "http://localhost:3000",  # Local frontend development
            "http://localhost:8080",  # Alternative local port
        ]
        logger.info("CORS: Staging mode - allowing staging domains")
    else:
        # Production: Allow only production domains
        allowed_origins = [
            "https://example.com",
            "https://api.example.com",
            "https://app.example.com",
        ]
        logger.info("CORS: Production mode - allowing production domains only")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,  # Allow cookies and authentication headers
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Allowed HTTP methods
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRFToken",
            "X-API-Key",
        ],  # Allowed headers
        expose_headers=[
            "X-Request-ID",
            "X-Response-Time",
            "X-Total-Count",
        ],  # Headers exposed to browser
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    logger.info("CORS middleware configured successfully")
    return app
