"""
Custom exception classes for the Feature Store API.
Provides user-friendly error messages and proper HTTP status codes.
"""

from fastapi import HTTPException
from typing import Optional, Dict, Any

class FeatureStoreException(HTTPException):
    """Base exception class for Feature Store API."""
    
    def __init__(self, status_code: int, detail: str, error_code: Optional[str] = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

class ItemNotFoundException(FeatureStoreException):
    """Exception raised when an item is not found."""
    
    def __init__(self, identifier: str, category: str, table_type: str = "bright_uid"):
        super().__init__(
            status_code=404,
            detail=f"Item not found: {identifier}/{category} in table '{table_type}'",
            error_code="ITEM_NOT_FOUND"
        )
        self.identifier = identifier
        self.category = category
        self.table_type = table_type

class InvalidTableTypeException(FeatureStoreException):
    """Exception raised when an invalid table type is provided."""
    
    def __init__(self, table_type: str):
        super().__init__(
            status_code=400,
            detail=f"Invalid table_type: '{table_type}'. Must be 'bright_uid' or 'account_id'",
            error_code="INVALID_TABLE_TYPE"
        )
        self.table_type = table_type

class ValidationException(FeatureStoreException):
    """Exception raised when request validation fails."""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=422,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
        self.field = field

class EmptyRequestException(FeatureStoreException):
    """Exception raised when request body is empty."""
    
    def __init__(self, field: str = "body"):
        super().__init__(
            status_code=400,
            detail=f"Request {field} cannot be empty",
            error_code="EMPTY_REQUEST"
        )
        self.field = field

class DynamoDBException(FeatureStoreException):
    """Exception raised when DynamoDB operations fail."""
    
    def __init__(self, operation: str, detail: str, original_error: Optional[Exception] = None):
        super().__init__(
            status_code=500,
            detail=f"DynamoDB {operation} failed: {detail}",
            error_code="DYNAMODB_ERROR"
        )
        self.operation = operation
        self.original_error = original_error

class MetricsException(FeatureStoreException):
    """Exception raised when metrics collection fails."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=500,
            detail=f"Metrics collection failed: {detail}",
            error_code="METRICS_ERROR"
        )

class ConfigurationException(FeatureStoreException):
    """Exception raised when configuration is invalid."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=500,
            detail=f"Configuration error: {detail}",
            error_code="CONFIGURATION_ERROR"
        )

class RateLimitException(FeatureStoreException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, limit: int, window: str = "minute"):
        super().__init__(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} requests per {window}",
            error_code="RATE_LIMIT_EXCEEDED"
        )
        self.limit = limit
        self.window = window

class AuthenticationException(FeatureStoreException):
    """Exception raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=401,
            detail=detail,
            error_code="AUTHENTICATION_FAILED"
        )

class AuthorizationException(FeatureStoreException):
    """Exception raised when authorization fails."""
    
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=403,
            detail=detail,
            error_code="AUTHORIZATION_FAILED"
        )

class ServiceUnavailableException(FeatureStoreException):
    """Exception raised when service is temporarily unavailable."""
    
    def __init__(self, service: str, retry_after: int = 60):
        super().__init__(
            status_code=503,
            detail=f"Service '{service}' is temporarily unavailable. Retry after {retry_after} seconds",
            error_code="SERVICE_UNAVAILABLE"
        )
        self.service = service
        self.retry_after = retry_after

class FeatureStoreErrorResponse:
    """Standardized error response format."""
    
    @staticmethod
    def create_error_response(
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        field: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a standardized error response."""
        from datetime import datetime
        
        response = {
            "error": {
                "status_code": status_code,
                "detail": detail,
                "timestamp": timestamp or datetime.utcnow().isoformat()
            }
        }
        
        if error_code:
            response["error"]["error_code"] = error_code
        
        if field:
            response["error"]["field"] = field
        
        return response
