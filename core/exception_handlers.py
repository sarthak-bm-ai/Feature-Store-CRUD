"""
Global exception handlers for the Feature Store API.
Provides centralized error handling and user-friendly responses.
"""

import traceback
from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

from .exceptions import (
    FeatureStoreException,
    ItemNotFoundException,
    InvalidTableTypeException,
    ValidationException,
    EmptyRequestException,
    DynamoDBException,
    MetricsException,
    ConfigurationException,
    RateLimitException,
    AuthenticationException,
    AuthorizationException,
    ServiceUnavailableException,
    FeatureStoreErrorResponse
)
from .logging_config import get_logger

# Configure logger
logger = get_logger("exception_handlers")

async def feature_store_exception_handler(request: Request, exc: FeatureStoreException) -> JSONResponse:
    """Handle custom Feature Store exceptions."""
    logger.warning(f"Feature Store exception: {exc.detail}", extra={
        "error_code": exc.error_code,
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content=FeatureStoreErrorResponse.create_error_response(
            status_code=exc.status_code,
            detail=exc.detail,
            error_code=exc.error_code
        )
    )

async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content=FeatureStoreErrorResponse.create_error_response(
            status_code=exc.status_code,
            detail=exc.detail
        )
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    detail = f"Validation error: {'; '.join(errors)}"
    
    logger.warning(f"Validation error: {detail}", extra={
        "path": request.url.path,
        "method": request.method,
        "errors": exc.errors()
    })
    
    return JSONResponse(
        status_code=422,
        content=FeatureStoreErrorResponse.create_error_response(
            status_code=422,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
    )

async def dynamodb_exception_handler(request: Request, exc: ClientError) -> JSONResponse:
    """Handle DynamoDB client errors."""
    error_code = exc.response.get('Error', {}).get('Code', 'Unknown')
    error_message = exc.response.get('Error', {}).get('Message', str(exc))
    
    # Map DynamoDB errors to appropriate HTTP status codes
    if error_code == 'ResourceNotFoundException':
        status_code = 404
        detail = "DynamoDB table not found"
    elif error_code == 'ValidationException':
        status_code = 400
        detail = f"DynamoDB validation error: {error_message}"
    elif error_code == 'ConditionalCheckFailedException':
        status_code = 409
        detail = "DynamoDB conditional check failed"
    elif error_code == 'ProvisionedThroughputExceededException':
        status_code = 429
        detail = "DynamoDB provisioned throughput exceeded"
    else:
        status_code = 500
        detail = f"DynamoDB error: {error_message}"
    
    logger.error(f"DynamoDB error: {error_code} - {error_message}", extra={
        "error_code": error_code,
        "status_code": status_code,
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=status_code,
        content=FeatureStoreErrorResponse.create_error_response(
            status_code=status_code,
            detail=detail,
            error_code="DYNAMODB_ERROR"
        )
    )

async def boto3_exception_handler(request: Request, exc: Boto3Error) -> JSONResponse:
    """Handle Boto3 errors."""
    logger.error(f"Boto3 error: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=500,
        content=FeatureStoreErrorResponse.create_error_response(
            status_code=500,
            detail="AWS service error",
            error_code="AWS_ERROR"
        )
    )

async def credentials_exception_handler(request: Request, exc: NoCredentialsError) -> JSONResponse:
    """Handle AWS credentials errors."""
    logger.error(f"AWS credentials error: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=500,
        content=FeatureStoreErrorResponse.create_error_response(
            status_code=500,
            detail="AWS credentials not configured",
            error_code="AWS_CREDENTIALS_ERROR"
        )
    )

async def connection_exception_handler(request: Request, exc: EndpointConnectionError) -> JSONResponse:
    """Handle AWS connection errors."""
    logger.error(f"AWS connection error: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=503,
        content=FeatureStoreErrorResponse.create_error_response(
            status_code=503,
            detail="AWS service unavailable",
            error_code="AWS_CONNECTION_ERROR"
        )
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    # Log the full exception with traceback
    logger.error(f"Unhandled exception: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method,
        "exception_type": type(exc).__name__,
        "traceback": traceback.format_exc()
    })
    
    # Don't expose internal details in production
    from .settings import settings
    if settings.is_development():
        detail = f"Internal server error: {str(exc)}"
    else:
        detail = "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content=FeatureStoreErrorResponse.create_error_response(
            status_code=500,
            detail=detail,
            error_code="INTERNAL_SERVER_ERROR"
        )
    )

def setup_exception_handlers(app):
    """Setup all exception handlers for the FastAPI app."""
    
    # Custom Feature Store exceptions
    app.add_exception_handler(FeatureStoreException, feature_store_exception_handler)
    app.add_exception_handler(ItemNotFoundException, feature_store_exception_handler)
    app.add_exception_handler(InvalidTableTypeException, feature_store_exception_handler)
    app.add_exception_handler(ValidationException, feature_store_exception_handler)
    app.add_exception_handler(EmptyRequestException, feature_store_exception_handler)
    app.add_exception_handler(DynamoDBException, feature_store_exception_handler)
    app.add_exception_handler(MetricsException, feature_store_exception_handler)
    app.add_exception_handler(ConfigurationException, feature_store_exception_handler)
    app.add_exception_handler(RateLimitException, feature_store_exception_handler)
    app.add_exception_handler(AuthenticationException, feature_store_exception_handler)
    app.add_exception_handler(AuthorizationException, feature_store_exception_handler)
    app.add_exception_handler(ServiceUnavailableException, feature_store_exception_handler)
    
    # Standard HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # AWS/DynamoDB exceptions
    app.add_exception_handler(ClientError, dynamodb_exception_handler)
    app.add_exception_handler(Boto3Error, boto3_exception_handler)
    app.add_exception_handler(NoCredentialsError, credentials_exception_handler)
    app.add_exception_handler(EndpointConnectionError, connection_exception_handler)
    
    # Global exception handler (must be last)
    app.add_exception_handler(Exception, global_exception_handler)
    
    logger.info("Exception handlers configured successfully")
    return app
