"""
API Standard Metrics Middleware for FastAPI.
Automatically tracks HTTP-level metrics for all API calls.
"""
import time
from fastapi import Request, Response
from core.metrics import metrics, MetricNames
from core.settings import settings
from core.logging_config import get_logger

# Configure logger
logger = get_logger("metrics_middleware")

class MetricsMiddleware:
    """Middleware for automatic HTTP metrics collection."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        """Track metrics for all HTTP requests automatically."""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = str(request.url.path)
        client_ip = request.client.host if request.client else "unknown"
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            # Handle exceptions and create error response
            status_code = 500
            error = str(e)
            logger.error(f"Request failed: {method} {path} - {error}")
            # Re-raise the exception to be handled by FastAPI
            raise
        
        # Calculate duration
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Track comprehensive metrics (synchronous)
        self._track_metrics(request, response, duration, status_code, error)
        
        return response
    
    def _track_metrics(self, request: Request, response: Response, duration: float, status_code: int, error: str = None):
        """Track comprehensive HTTP metrics."""
        method = request.method
        path = str(request.url.path)
        client_ip = request.client.host if request.client else "unknown"
        
        # Create base tags
        base_tags = {
            "method": method,
            "path": self._normalize_path(path),
            "status_code": str(status_code),
            "client_ip": client_ip
        }
        
        # Add status category tag
        status_category = self._get_status_category(status_code)
        base_tags["status_category"] = status_category
        
        # Track request count
        metrics.increment_counter(
            "http.request.count",
            tags=base_tags
        )
        
        # Track request duration
        metrics.timing(
            "http.request.duration",
            duration,
            tags=base_tags
        )
        
        # Track response size (if available)
        if hasattr(response, "body") and response.body:
            response_size = len(response.body) if isinstance(response.body, bytes) else len(str(response.body))
            metrics.gauge(
                "http.response.size",
                response_size,
                tags=base_tags
            )
        
        # Track error metrics
        if status_code >= 400:
            metrics.increment_counter(
                "http.error.count",
                tags={
                    **base_tags,
                    "error_type": self._get_error_type(status_code),
                    "error_message": error[:100] if error else "unknown"
                }
            )
        
        # Track success metrics
        if status_code < 400:
            metrics.increment_counter(
                "http.success.count",
                tags=base_tags
            )
        
        # Track slow requests (>1 second)
        if duration > 1000:
            metrics.increment_counter(
                "http.slow_request.count",
                tags={
                    **base_tags,
                    "duration_ms": str(int(duration))
                }
            )
        
        # Track specific endpoint metrics
        endpoint = self._get_endpoint_name(path)
        if endpoint:
            endpoint_tags = {
                **base_tags,
                "endpoint": endpoint
            }
            
            metrics.increment_counter(
                "http.endpoint.count",
                tags=endpoint_tags
            )
            
            metrics.timing(
                "http.endpoint.duration",
                duration,
                tags=endpoint_tags
            )
        
        # Track API version metrics
        api_version = self._get_api_version(path)
        if api_version:
            version_tags = {
                **base_tags,
                "api_version": api_version
            }
            
            metrics.increment_counter(
                "http.api_version.count",
                tags=version_tags
            )
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for consistent metrics (remove IDs, etc.)."""
        # Replace UUIDs and IDs with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path)
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace common ID patterns
        path = re.sub(r'/[a-zA-Z0-9_-]+-\d+', '/{identifier}', path)
        
        return path
    
    def _get_status_category(self, status_code: int) -> str:
        """Get status category for metrics grouping."""
        if 200 <= status_code < 300:
            return "2xx"
        elif 300 <= status_code < 400:
            return "3xx"
        elif 400 <= status_code < 500:
            return "4xx"
        elif 500 <= status_code < 600:
            return "5xx"
        else:
            return "unknown"
    
    def _get_error_type(self, status_code: int) -> str:
        """Get error type for metrics grouping."""
        if status_code == 400:
            return "bad_request"
        elif status_code == 401:
            return "unauthorized"
        elif status_code == 403:
            return "forbidden"
        elif status_code == 404:
            return "not_found"
        elif status_code == 422:
            return "validation_error"
        elif status_code == 429:
            return "rate_limit"
        elif status_code == 500:
            return "internal_error"
        elif status_code == 502:
            return "bad_gateway"
        elif status_code == 503:
            return "service_unavailable"
        else:
            return "unknown_error"
    
    def _get_endpoint_name(self, path: str) -> str:
        """Extract endpoint name from path."""
        # Remove API version prefix
        if path.startswith("/api/v"):
            path = path.split("/", 3)[-1] if len(path.split("/")) > 3 else path
        
        # Extract endpoint name
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            return f"{parts[0]}_{parts[1]}"
        elif len(parts) == 1:
            return parts[0]
        else:
            return "root"
    
    def _get_api_version(self, path: str) -> str:
        """Extract API version from path."""
        if path.startswith("/api/v"):
            try:
                return path.split("/")[2]  # Extract version from /api/v1/...
            except IndexError:
                return None
        return None

def setup_metrics_middleware(app):
    """Setup metrics middleware for the FastAPI app."""
    # Add the middleware
    app.middleware("http")(MetricsMiddleware(app))
    
    logger.info("HTTP metrics middleware enabled")
    
    return app

