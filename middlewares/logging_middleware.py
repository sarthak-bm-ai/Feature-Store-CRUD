"""
Request/Response Logging Middleware for FastAPI.
Provides comprehensive logging of HTTP requests and responses.
"""
import time
import logging
import json
from typing import Dict, Any
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from core.settings import settings
from core.logging_config import get_logger

# Configure logger
logger = get_logger("middleware")

class RequestResponseLogger:
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        """Log request and response details."""
        start_time = time.time()
        request_id = self._generate_request_id()
        
        # Log request details (synchronous)
        self._log_request(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response details (synchronous)
        self._log_response(request, response, duration, request_id)
        
        return response
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracing."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _log_request(self, request: Request, request_id: str):
        """Log incoming request details."""
        # Extract request information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get request body for POST/PUT requests (if not too large)
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body only if it's not too large
                if hasattr(request, "_body"):
                    body = request._body
                else:
                    # For streaming requests, we'll skip body logging
                    body = "<streaming>"
            except Exception:
                body = "<error reading body>"
        
        # Create request log entry
        request_log = {
            "request_id": request_id,
            "type": "request",
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "headers": dict(request.headers),
            "body": body if body and len(str(body)) < 1000 else "<body too large or empty>",
            "timestamp": time.time()
        }
        
        # Log with appropriate level
        if settings.is_development():
            logger.info(f"📥 REQUEST [{request_id}] {request.method} {request.url.path}", extra=request_log)
        else:
            logger.info(f"REQUEST [{request_id}] {request.method} {request.url.path}", extra=request_log)
    
    def _log_response(self, request: Request, response: Response, duration: float, request_id: str):
        """Log outgoing response details."""
        # Extract response information
        status_code = response.status_code
        content_type = response.headers.get("content-type", "unknown")
        
        # Get response body for logging (if not too large)
        response_body = None
        if hasattr(response, "body"):
            try:
                if len(response.body) < 1000:  # Only log small responses
                    response_body = response.body.decode("utf-8") if isinstance(response.body, bytes) else str(response.body)
                else:
                    response_body = "<response too large>"
            except Exception:
                response_body = "<error reading response body>"
        elif isinstance(response, StreamingResponse):
            response_body = "<streaming response>"
        else:
            response_body = "<no body>"
        
        # Create response log entry
        response_log = {
            "request_id": request_id,
            "type": "response",
            "method": request.method,
            "path": str(request.url.path),
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "content_type": content_type,
            "headers": dict(response.headers),
            "body": response_body,
            "timestamp": time.time()
        }
        
        # Log with appropriate level based on status code
        if status_code >= 500:
            logger.error(f"📤 RESPONSE [{request_id}] {status_code} in {duration:.2f}s", extra=response_log)
        elif status_code >= 400:
            logger.warning(f"📤 RESPONSE [{request_id}] {status_code} in {duration:.2f}s", extra=response_log)
        else:
            if settings.is_development():
                logger.info(f"📤 RESPONSE [{request_id}] {status_code} in {duration:.2f}s", extra=response_log)
            else:
                logger.info(f"RESPONSE [{request_id}] {status_code} in {duration:.2f}s", extra=response_log)

def setup_logging_middleware(app):
    """Setup logging middleware for the FastAPI app."""
    # Add the middleware
    app.middleware("http")(RequestResponseLogger(app))
    
    # Logging is already configured in core.logging_config
    logger.info("Request/Response logging middleware enabled")
    
    return app
