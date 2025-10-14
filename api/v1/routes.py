from fastapi import APIRouter, HTTPException, Query
from components.features.controller import FeatureController
from components.features.schemas import (
    WriteRequestSchema, ReadRequestSchema, WriteResponseSchema, 
    ReadResponseSchema, HealthResponseSchema, ErrorResponseSchema
)
from core.metrics import time_function, MetricNames
from core.config import health_check, get_all_tables
from core.timestamp_utils import get_current_timestamp
from typing import Dict, List

router = APIRouter()

# 1) GET /get/item/{entity_value}/{category} → return all features of that category
@router.get("/get/item/{entity_value}/{category}")
@time_function(MetricNames.READ_SINGLE_ITEM)
def get_category_features(entity_value: str, category: str, entity_type: str = Query(default="bright_uid", description="Entity type: 'bright_uid' or 'account_id'")):
    """Get all features for a specific category."""
    try:
        return FeatureController.get_single_category(entity_value, category, entity_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# 2) POST /get/items with body containing entity_type and mapping
# Body: {metadata: {source: "api"}, data: {entity_type: "bright_uid", entity_value: "user123", feature_list: ["cat1:f1", "cat1:f2", "cat2:*"]}}
@router.post("/get/items", response_model=ReadResponseSchema)
@time_function(MetricNames.READ_MULTI_CATEGORY)
def get_items_by_feature_mapping(request_data: ReadRequestSchema):
    """Get filtered features from multiple categories."""
    try:
        return FeatureController.get_multiple_categories(request_data.dict())
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))


# 3) POST /items write → replace entire features map per category
# Body: {metadata: {source: "prediction_service"}, data: {entity_type: "bright_uid", entity_value: "user123", feature_list: [{"category": "cat1", "features": {"f1": "v1", "f2": "v2"}}]}}
@router.post("/items", response_model=WriteResponseSchema)
@time_function(MetricNames.WRITE_MULTI_CATEGORY)
def upsert_items(request_data: WriteRequestSchema):
    """Write/update features with automatic metadata handling."""
    try:
        return FeatureController.upsert_features(request_data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check endpoint for DynamoDB connection
@router.get("/health", response_model=HealthResponseSchema)
def health_check_endpoint():
    """Check DynamoDB connection health."""
    try:
        is_healthy = health_check()
        tables = get_all_tables()
        
        return HealthResponseSchema(
            status="healthy" if is_healthy else "unhealthy",
            dynamodb_connection=is_healthy,
            tables_available=list(tables.keys()),
            timestamp=get_current_timestamp()
        )
    except Exception as e:
        return HealthResponseSchema(
            status="unhealthy",
            dynamodb_connection=False,
            tables_available=[],
            timestamp=get_current_timestamp()
        )
