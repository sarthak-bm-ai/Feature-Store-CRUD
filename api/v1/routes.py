from fastapi import APIRouter, HTTPException, Query
from components.features.controller import FeatureController
from core.metrics import time_function, MetricNames
from core.config import health_check, get_all_tables
from typing import Dict, List
from datetime import datetime

router = APIRouter()

# 1) GET /get/item/{identifier}/{category} → return all features of that category
@router.get("/get/item/{identifier}/{category}")
@time_function(MetricNames.READ_SINGLE_ITEM)
def get_category_features(identifier: str, category: str, table_type: str = Query(default="bright_uid", description="Table type: 'bright_uid' or 'account_id'")):
    """Get all features for a specific category."""
    try:
        return FeatureController.get_single_category(identifier, category, table_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# 2) POST /get/items with body containing identifier and mapping
# Body: {metadata: {source: "api"}, data: {identifier: "bright_uid", identifier_value: "user123", feature_list: ["cat1:f1", "cat1:f2", "cat2:f3"]}}
@router.post("/get/items")
@time_function(MetricNames.READ_MULTI_CATEGORY)
def get_items_by_feature_mapping(request_data: Dict):
    """Get filtered features from multiple categories."""
    try:
        return FeatureController.get_multiple_categories(request_data)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))


# 3) POST /items write → replace entire features map per category
# Body: {metadata: {source: "api"}, data: {identifier: "bright_uid", identifier_value: "user123", feature_list: [{"category": "cat1", "features": {"f1": "v1", "f2": "v2"}}]}}
@router.post("/items")
@time_function(MetricNames.WRITE_MULTI_CATEGORY)
def upsert_items(request_data: Dict):
    """Write/update features with automatic metadata handling."""
    try:
        return FeatureController.upsert_features(request_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check endpoint for DynamoDB connection
@router.get("/health")
def health_check_endpoint():
    """Check DynamoDB connection health."""
    try:
        is_healthy = health_check()
        tables = get_all_tables()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "dynamodb_connection": is_healthy,
            "tables_available": list(tables.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "dynamodb_connection": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
