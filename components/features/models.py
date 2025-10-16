from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Core data models
class FeatureMeta(BaseModel):
    """
    Meta information for feature records.
    All timestamps are in ISO 8601 format with milliseconds precision.
    """
    created_at: datetime = Field(..., description="Creation timestamp in ISO 8601 format")
    updated_at: datetime = Field(..., description="Last update timestamp in ISO 8601 format")
    compute_id: Optional[str] = Field(None, description="ID of the compute job that generated the features")
    
    @validator('created_at', 'updated_at', pre=True)
    def parse_timestamp(cls, v):
        """Ensure timestamps are properly parsed from ISO 8601 strings."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # Try alternate formats
                from datetime import timezone
                try:
                    dt = datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%f")
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    try:
                        dt = datetime.strptime(v, "%Y-%m-%dT%H:%M:%S")
                        return dt.replace(tzinfo=timezone.utc)
                    except ValueError:
                        raise ValueError(f"Invalid timestamp format: {v}. Expected ISO 8601 format.")
        return v

class Features(BaseModel):
    data: Dict[str, Any]  # actual feature values
    meta: FeatureMeta

class Item(BaseModel):
    bright_uid: Optional[str] = None
    account_pid: Optional[str] = None
    category: str
    features: Features

# Request models
class RequestMeta(BaseModel):
    source: str = Field(..., description="Source of the request", example="api")

class WriteRequestMeta(BaseModel):
    source: str = Field(..., description="Source of the request", example="prediction_service")
    compute_id: Optional[str] = Field(None, description="ID of the compute job that generated the features")
    
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
    meta: WriteRequestMeta
    data: Dict[str, Any]
    
    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError('Data cannot be empty')
        
        required_fields = ['entity_type', 'entity_value', 'category', 'features']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        
        if v['entity_type'] not in ['bright_uid', 'account_pid']:
            raise ValueError('entity_type must be either "bright_uid" or "account_pid"')
        
        if not v['entity_value'] or not isinstance(v['entity_value'], str):
            raise ValueError('entity_value must be a non-empty string')
        
        if not v['category'] or not isinstance(v['category'], str):
            raise ValueError('category must be a non-empty string')
        
        if not v['features'] or not isinstance(v['features'], dict):
            raise ValueError('features must be a non-empty dictionary')
        
        return v

class ReadRequest(BaseModel):
    meta: RequestMeta
    data: Dict[str, Any]
    
    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError('Data cannot be empty')
        
        required_fields = ['entity_type', 'entity_value', 'feature_list']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        
        if v['entity_type'] not in ['bright_uid', 'account_pid']:
            raise ValueError('Identifier must be either "bright_uid" or "account_pid"')
        
        if not v['entity_value'] or not isinstance(v['entity_value'], str):
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
    message: str = Field(..., description="Success message", example="Category written successfully (full replace)")
    entity_value: str = Field(..., description="User/account identifier", example="user123")
    entity_type: str = Field(..., description="Entity type used", example="bright_uid")
    category: str = Field(..., description="Category name", example="d0_unauth_features")
    feature_count: int = Field(..., description="Number of features written", example=5)

class ReadResponse(BaseModel):
    entity_value: str = Field(..., description="User/account identifier", example="user123")
    entity_type: str = Field(..., description="Entity type used", example="bright_uid")
    items: Dict[str, Item] = Field(..., description="Retrieved items")
    unavailable_feature_categories: List[str] = Field(..., description="Categories not found", example=[])

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status", example="healthy")
    dynamodb_connection: bool = Field(..., description="DynamoDB connection status", example=True)
    tables_available: List[str] = Field(..., description="Available tables", example=["bright_uid", "account_pid"])
    timestamp: str = Field(..., description="Response timestamp", example="2025-10-08T19:17:20.239310")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message", example="Item not found: user123/user_features")
