from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Core data models
class FeatureMetadata(BaseModel):
    created_at: datetime
    updated_at: datetime
    compute_id: Optional[str] = None

class Features(BaseModel):
    data: Dict[str, Any]  # actual feature values
    metadata: FeatureMetadata

class Item(BaseModel):
    bright_uid: Optional[str] = None
    account_id: Optional[str] = None
    category: str
    features: Features

# Request models
class RequestMetadata(BaseModel):
    source: str = Field(..., description="Source of the request", example="api")

class WriteRequestMetadata(BaseModel):
    source: str = Field(..., description="Source of the request", example="prediction_service")
    
    @validator('source')
    def validate_source(cls, v):
        if v != "prediction_service":
            raise ValueError('Only prediction_service is allowed for write operations')
        return v

class FeatureItem(BaseModel):
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

class WriteRequest(BaseModel):
    metadata: WriteRequestMetadata
    data: Dict[str, Any]
    
    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError('Data cannot be empty')
        
        required_fields = ['identifier', 'identifier_value', 'feature_list']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        
        if v['identifier'] not in ['bright_uid', 'account_id']:
            raise ValueError('Identifier must be either "bright_uid" or "account_id"')
        
        if not v['identifier_value'] or not isinstance(v['identifier_value'], str):
            raise ValueError('Identifier value must be a non-empty string')
        
        if not v['feature_list'] or not isinstance(v['feature_list'], list):
            raise ValueError('Feature list must be a non-empty list')
        
        return v

class ReadRequest(BaseModel):
    metadata: RequestMetadata
    data: Dict[str, Any]
    
    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError('Data cannot be empty')
        
        required_fields = ['identifier', 'identifier_value', 'feature_list']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        
        if v['identifier'] not in ['bright_uid', 'account_id']:
            raise ValueError('Identifier must be either "bright_uid" or "account_id"')
        
        if not v['identifier_value'] or not isinstance(v['identifier_value'], str):
            raise ValueError('Identifier value must be a non-empty string')
        
        if not v['feature_list'] or not isinstance(v['feature_list'], list):
            raise ValueError('Feature list must be a non-empty list')
        
        for feature in v['feature_list']:
            if not isinstance(feature, str):
                raise ValueError('Feature must be a string in format "category:feature" or "category:*"')
            if ':' not in feature:
                raise ValueError('Feature must be in format "category:feature" or "category:*"')
            # Allow wildcard pattern
            if feature.endswith(':') and not feature.endswith(':*'):
                raise ValueError('Invalid feature format. Use "category:*" for wildcard or "category:feature" for specific feature')
        
        return v

# Response models
class WriteResponse(BaseModel):
    message: str = Field(..., description="Success message", example="Items written successfully (full replace per category)")
    identifier: str = Field(..., description="User/account identifier", example="user123")
    table_type: str = Field(..., description="Table type used", example="bright_uid")
    results: Dict[str, Dict[str, Any]] = Field(..., description="Results per category")
    total_features: int = Field(..., description="Total number of features written", example=5)

class ReadResponse(BaseModel):
    identifier: str = Field(..., description="User/account identifier", example="user123")
    table_type: str = Field(..., description="Table type used", example="bright_uid")
    items: Dict[str, Item] = Field(..., description="Retrieved items")
    missing_categories: List[str] = Field(..., description="Categories not found", example=[])

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status", example="healthy")
    dynamodb_connection: bool = Field(..., description="DynamoDB connection status", example=True)
    tables_available: List[str] = Field(..., description="Available tables", example=["bright_uid", "account_id"])
    timestamp: str = Field(..., description="Response timestamp", example="2025-10-08T19:17:20.239310")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message", example="Item not found: user123/user_features")
