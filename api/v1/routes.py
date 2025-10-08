from fastapi import APIRouter, Query
from components.features import crud
from core.metrics import metrics, time_function, MetricNames
from components.features.models import Item, Features, FeatureMetadata
from core.config import health_check, get_all_tables
from core.exceptions import (
    ItemNotFoundException,
    InvalidTableTypeException,
    EmptyRequestException,
    ValidationException
)
from typing import Dict, List, Optional
from datetime import datetime

router = APIRouter()

# Helper functions removed - now using optimized DynamoDB UpdateItem with if_not_exists

def filter_features_new_schema(item: dict, feature_keys: set):
    """Filter features in the new schema (data.metadata structure)"""
    if not feature_keys or "features" not in item:
        return item
    
    filtered = dict(item)
    features = filtered.get("features", {})
    if isinstance(features, dict) and "data" in features:
        filtered_data = {k: v for k, v in features["data"].items() if k in feature_keys}
        filtered["features"]["data"] = filtered_data
    return filtered

# 1) GET /get/item/{identifier}/{category} → return all features of that category
@router.get("/get/item/{identifier}/{category}")
@time_function(MetricNames.READ_SINGLE_ITEM)
def get_category_features(identifier: str, category: str, table_type: str = Query(default="bright_uid", description="Table type: 'bright_uid' or 'account_id'")):
    if table_type not in ["bright_uid", "account_id"]:
        raise InvalidTableTypeException(table_type)
    
    item = crud.get_item(identifier, category, table_type)
    if not item:
        metrics.increment_counter(f"{MetricNames.READ_SINGLE_ITEM}.not_found", tags={"identifier": identifier, "category": category, "table_type": table_type})
        raise ItemNotFoundException(identifier, category, table_type)
    metrics.increment_counter(f"{MetricNames.READ_SINGLE_ITEM}.success", tags={"identifier": identifier, "category": category, "table_type": table_type})
    return item


# 2) POST /get/item/{identifier} with body mapping → return mentioned features only
# Body: { "cat1": ["f1", "f2"], "cat2": ["f3"] }
@router.post("/get/item/{identifier}")
@time_function(MetricNames.READ_MULTI_CATEGORY)
def get_items_by_feature_mapping(identifier: str, mapping: Dict[str, List[str]], table_type: str = Query(default="bright_uid", description="Table type: 'bright_uid' or 'account_id'")):
    if table_type not in ["bright_uid", "account_id"]:
        raise InvalidTableTypeException(table_type)
    
    if not mapping:
        metrics.increment_counter(f"{MetricNames.READ_MULTI_CATEGORY}.error", tags={"error_type": "empty_mapping", "table_type": table_type})
        raise EmptyRequestException("mapping body")

    results: Dict[str, dict] = {}
    missing: List[str] = []

    for category, features in mapping.items():
        item = crud.get_item(identifier, category, table_type)
        if not item:
            missing.append(category)
            continue
        if features:
            item = filter_features_new_schema(item, set(features))
        results[category] = item

    if not results:
        metrics.increment_counter(f"{MetricNames.READ_MULTI_CATEGORY}.not_found", tags={"identifier": identifier, "table_type": table_type})
        raise ItemNotFoundException(identifier, "any category", table_type)

    metrics.increment_counter(f"{MetricNames.READ_MULTI_CATEGORY}.success", tags={"identifier": identifier, "table_type": table_type})
    return {"identifier": identifier, "table_type": table_type, "items": results, "missing_categories": missing}


# 3) POST /items/{identifier} write → replace entire features map per category
# Body: { "cat1": {...}, "cat2": {...} } (simple feature data)
# Metadata is auto-generated: new category gets fresh timestamps, existing preserves created_at
@router.post("/items/{identifier}")
@time_function(MetricNames.WRITE_MULTI_CATEGORY)
def upsert_items(identifier: str, items: Dict[str, Dict], table_type: str = Query(default="bright_uid", description="Table type: 'bright_uid' or 'account_id'")):
    if table_type not in ["bright_uid", "account_id"]:
        raise InvalidTableTypeException(table_type)
    
    if not items:
        metrics.increment_counter(f"{MetricNames.WRITE_MULTI_CATEGORY}.error", tags={"error_type": "empty_body", "table_type": table_type})
        raise EmptyRequestException("request body")

    results: Dict[str, dict] = {}
    total_features = 0
    
    for category, features in items.items():
        if not isinstance(features, dict):
            raise ValidationException(f"Features for category '{category}' must be an object", field=category)
        
        # Use optimized upsert with automatic metadata handling
        crud.upsert_item_with_metadata(identifier, category, features, table_type)
        
        total_features += len(features)
        results[category] = {"status": "replaced", "feature_count": len(features)}

    metrics.increment_counter(f"{MetricNames.WRITE_MULTI_CATEGORY}.success", tags={"identifier": identifier, "table_type": table_type, "categories_count": str(len(items))})
    return {"message": "Items written successfully (full replace per category)", "identifier": identifier, "table_type": table_type, "results": results, "total_features": total_features}


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
