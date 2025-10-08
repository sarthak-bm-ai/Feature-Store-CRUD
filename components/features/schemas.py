"""
Pydantic schemas for request and response validation.
Provides type safety and automatic API documentation.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

class MetadataSchema(BaseModel):
    """Metadata schema for requests."""
    source: str = Field(..., description="Source of the request", example="api")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "api"
            }
        }

class WriteMetadataSchema(BaseModel):
    """Metadata schema for write operations - only allows prediction_service."""
    source: str = Field(..., description="Source of the request", example="prediction_service")
    
    @validator('source')
    def validate_source(cls, v):
        if v != "prediction_service":
            raise ValueError('Only prediction_service is allowed for write operations')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "prediction_service"
            }
        }

class FeatureItemSchema(BaseModel):
    """Schema for individual feature items in write operations."""
    category: str = Field(..., description="Feature category", example="user_features")
    features: Dict[str, Any] = Field(..., description="Feature data", example={"age": 30, "income": 60000})
    
    @validator('category')
    def validate_category(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Category must be a non-empty string')
        if len(v) > 100:
            raise ValueError('Category name too long (max 100 characters)')
        return v.strip()
    
    @validator('features')
    def validate_features(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError('Features must be a non-empty dictionary')
        if len(v) == 0:
            raise ValueError('Features dictionary cannot be empty')
        return v

class WriteRequestSchema(BaseModel):
    """Schema for write operations (POST /items)."""
    metadata: WriteMetadataSchema = Field(..., description="Request metadata")
    data: Dict[str, Any] = Field(..., description="Request data")
    
    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError('Data cannot be empty')
        
        required_fields = ['identifier', 'identifier_value', 'feature_list']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        
        # Validate identifier
        if v['identifier'] not in ['bright_uid', 'account_id']:
            raise ValueError('Identifier must be either "bright_uid" or "account_id"')
        
        # Validate identifier_value
        if not v['identifier_value'] or not isinstance(v['identifier_value'], str):
            raise ValueError('Identifier value must be a non-empty string')
        
        # Validate feature_list
        if not v['feature_list'] or not isinstance(v['feature_list'], list):
            raise ValueError('Feature list must be a non-empty list')
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "source": "prediction_service"
                },
                "data": {
                    "identifier": "bright_uid",
                    "identifier_value": "user123",
                    "feature_list": [
                        {
                            "category": "user_features",
                            "features": {
                                "age": 30,
                                "income": 60000,
                                "city": "SF"
                            }
                        }
                    ]
                }
            }
        }

class ReadRequestSchema(BaseModel):
    """Schema for read operations (POST /get/items)."""
    metadata: MetadataSchema = Field(..., description="Request metadata")
    data: Dict[str, Any] = Field(..., description="Request data")
    
    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError('Data cannot be empty')
        
        required_fields = ['identifier', 'identifier_value', 'feature_list']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        
        # Validate identifier
        if v['identifier'] not in ['bright_uid', 'account_id']:
            raise ValueError('Identifier must be either "bright_uid" or "account_id"')
        
        # Validate identifier_value
        if not v['identifier_value'] or not isinstance(v['identifier_value'], str):
            raise ValueError('Identifier value must be a non-empty string')
        
        # Validate feature_list
        if not v['feature_list'] or not isinstance(v['feature_list'], list):
            raise ValueError('Feature list must be a non-empty list')
        
        # Validate feature list format for read operations
        for feature in v['feature_list']:
            if not isinstance(feature, str):
                raise ValueError('Feature must be a string in format "category:feature"')
            if ':' not in feature:
                raise ValueError('Feature must be in format "category:feature"')
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "source": "api"
                },
                "data": {
                    "identifier": "bright_uid",
                    "identifier_value": "user123",
                    "feature_list": [
                        "user_features:age",
                        "user_features:income",
                        "trans_features:avg_credit_30d"
                    ]
                }
            }
        }

class FeatureMetadataSchema(BaseModel):
    """Schema for feature metadata."""
    created_at: str = Field(..., description="Creation timestamp", example="2025-10-08T19:17:20.239310")
    updated_at: str = Field(..., description="Last update timestamp", example="2025-10-08T19:17:20.239310")
    source: str = Field(..., description="Source of the feature", example="api")
    compute_id: str = Field(..., description="Compute ID", example="None")
    ttl: str = Field(..., description="Time to live", example="None")

class FeatureDataSchema(BaseModel):
    """Schema for feature data."""
    data: Dict[str, Any] = Field(..., description="Feature values")
    metadata: FeatureMetadataSchema = Field(..., description="Feature metadata")

class FeatureItemResponseSchema(BaseModel):
    """Schema for individual feature items in responses."""
    bright_uid: Optional[str] = Field(None, description="User identifier")
    account_id: Optional[str] = Field(None, description="Account identifier")
    category: str = Field(..., description="Feature category")
    features: FeatureDataSchema = Field(..., description="Feature data and metadata")

class WriteResponseSchema(BaseModel):
    """Schema for write operation responses."""
    message: str = Field(..., description="Success message", example="Items written successfully (full replace per category)")
    identifier: str = Field(..., description="User/account identifier", example="user123")
    table_type: str = Field(..., description="Table type used", example="bright_uid")
    results: Dict[str, Dict[str, Any]] = Field(..., description="Results per category")
    total_features: int = Field(..., description="Total number of features written", example=5)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Items written successfully (full replace per category)",
                "identifier": "user123",
                "table_type": "bright_uid",
                "results": {
                    "user_features": {
                        "status": "replaced",
                        "feature_count": 3
                    }
                },
                "total_features": 3
            }
        }

class ReadResponseSchema(BaseModel):
    """Schema for read operation responses."""
    identifier: str = Field(..., description="User/account identifier", example="user123")
    table_type: str = Field(..., description="Table type used", example="bright_uid")
    items: Dict[str, FeatureItemResponseSchema] = Field(..., description="Retrieved items")
    missing_categories: List[str] = Field(..., description="Categories not found", example=[])
    
    class Config:
        json_schema_extra = {
            "example": {
                "identifier": "user123",
                "table_type": "bright_uid",
                "items": {
                    "user_features": {
                        "bright_uid": "user123",
                        "category": "user_features",
                        "features": {
                            "data": {
                                "age": 30,
                                "income": 60000
                            },
                            "metadata": {
                                "created_at": "2025-10-08T19:17:20.239310",
                                "updated_at": "2025-10-08T19:17:20.239310",
                                "source": "api",
                                "compute_id": "None",
                                "ttl": "None"
                            }
                        }
                    }
                },
                "missing_categories": []
            }
        }

class HealthResponseSchema(BaseModel):
    """Schema for health check responses."""
    status: str = Field(..., description="Health status", example="healthy")
    dynamodb_connection: bool = Field(..., description="DynamoDB connection status", example=True)
    tables_available: List[str] = Field(..., description="Available tables", example=["bright_uid", "account_id"])
    timestamp: str = Field(..., description="Response timestamp", example="2025-10-08T19:17:20.239310")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "dynamodb_connection": True,
                "tables_available": ["bright_uid", "account_id"],
                "timestamp": "2025-10-08T19:17:20.239310"
            }
        }

class ErrorResponseSchema(BaseModel):
    """Schema for error responses."""
    detail: str = Field(..., description="Error message", example="Item not found: user123/user_features")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Item not found: user123/user_features"
            }
        }
