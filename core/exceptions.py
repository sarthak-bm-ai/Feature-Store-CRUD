"""
Custom exception hierarchy for Feature Store API.

This module defines custom exceptions that map to appropriate HTTP status codes,
providing better error handling and clearer error messages to API consumers.
"""

from typing import Optional


class FeatureStoreException(Exception):
    """Base exception for all Feature Store errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(FeatureStoreException):
    """
    Raised when input validation fails (e.g., invalid format, missing fields).
    Maps to HTTP 400 Bad Request.
    """
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class NotFoundError(FeatureStoreException):
    """
    Raised when a requested resource is not found (e.g., item doesn't exist).
    Maps to HTTP 404 Not Found.
    """
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ConflictError(FeatureStoreException):
    """
    Raised when there's a conflict with existing data.
    Maps to HTTP 409 Conflict.
    """
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class UnauthorizedError(FeatureStoreException):
    """
    Raised when authentication fails or is missing.
    Maps to HTTP 401 Unauthorized.
    """
    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class ForbiddenError(FeatureStoreException):
    """
    Raised when user doesn't have permission to access a resource.
    Maps to HTTP 403 Forbidden.
    """
    def __init__(self, message: str):
        super().__init__(message, status_code=403)


class InternalServerError(FeatureStoreException):
    """
    Raised when an unexpected internal error occurs.
    Maps to HTTP 500 Internal Server Error.
    """
    def __init__(self, message: str = "An internal server error occurred"):
        super().__init__(message, status_code=500)


class ServiceUnavailableError(FeatureStoreException):
    """
    Raised when a service dependency is unavailable (e.g., DynamoDB down).
    Maps to HTTP 503 Service Unavailable.
    """
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, status_code=503)


def categorize_error(error: Exception) -> FeatureStoreException:
    """
    Categorize a generic exception into an appropriate FeatureStoreException.
    
    This function analyzes the error message and type to determine the most
    appropriate HTTP status code and exception type.
    
    Priority order (first match wins):
    1. Already a FeatureStoreException
    2. Not found patterns (404)
    3. DynamoDB/AWS errors (503)
    4. Permission/authorization patterns (403)
    5. Validation patterns (400)
    6. KeyError/TypeError (400)
    7. Default to 500
    
    Args:
        error: The original exception
        
    Returns:
        FeatureStoreException: Categorized exception with appropriate status code
    """
    error_msg = str(error).lower()
    
    # Already a FeatureStoreException - return as is
    if isinstance(error, FeatureStoreException):
        return error
    
    # Check for "not found" patterns - 404
    # These should be checked first as they're the most specific
    not_found_patterns = [
        "not found",
        "does not exist",
        "doesn't exist",
        "no items found",
        "item not found"
    ]
    if any(pattern in error_msg for pattern in not_found_patterns):
        return NotFoundError(str(error))
    
    # Check for DynamoDB/AWS errors - 503
    # Check before validation patterns as these are service-level issues
    if "dynamodb" in error_msg or "aws" in error_msg or "boto" in error_msg:
        return ServiceUnavailableError(f"Database service error: {error}")
    
    # Check for permission/authorization patterns - 403
    # Check before validation patterns to prioritize authorization issues
    forbidden_patterns = [
        "forbidden",
        "permission denied",
        "access denied",
        "unauthorized category"
    ]
    if any(pattern in error_msg for pattern in forbidden_patterns):
        return ForbiddenError(str(error))
    
    # Check for validation patterns - 400
    # More general patterns, checked after more specific ones
    validation_patterns = [
        "invalid",
        "must be",
        "cannot be empty",
        "required field",
        "missing",
        "format",
        "expected",
        "too long",
        "too short",
        "out of range",
        "not allowed"  # Category validation
    ]
    if any(pattern in error_msg for pattern in validation_patterns):
        return ValidationError(str(error))
    
    # KeyError typically means missing required field - 400
    if isinstance(error, KeyError):
        return ValidationError(f"Missing required field: {error}")
    
    # TypeError typically means wrong type - 400
    if isinstance(error, TypeError):
        return ValidationError(f"Invalid data type: {error}")
    
    # Default to 500 Internal Server Error for uncategorized exceptions
    return InternalServerError(f"Unexpected error: {error}")

