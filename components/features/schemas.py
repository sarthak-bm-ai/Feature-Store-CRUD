"""
Pydantic schemas for request and response validation.
Uses models from models.py for consistency and reusability.
"""
from .models import (
    WriteRequest, ReadRequest, WriteResponse, ReadResponse, 
    HealthResponse, ErrorResponse
)

# Export models as schemas for API endpoints
WriteRequestSchema = WriteRequest
ReadRequestSchema = ReadRequest
WriteResponseSchema = WriteResponse
ReadResponseSchema = ReadResponse
HealthResponseSchema = HealthResponse
ErrorResponseSchema = ErrorResponse
