from fastapi import APIRouter, HTTPException, Query
from app import crud
from app.utils import filter_features
from app.metrics import metrics, time_function, MetricNames
from app.models import Item, Features, FeatureMetadata
from typing import Dict, List, Optional
from datetime import datetime

router = APIRouter()

def create_features_with_metadata(data: Dict, source: str = "api", compute_id: str = None, ttl: int = None):
    """Helper to create features with metadata for NEW items"""
    now = datetime.utcnow()
    return {
        "data": data,
        "metadata": {
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "source": source,
            "compute_id": compute_id,
            "ttl": ttl
        }
    }

def update_features_with_metadata(data: Dict, existing_metadata: Dict, source: str = "api", compute_id: str = None, ttl: int = None):
    """Helper to update features with metadata for EXISTING items - preserves created_at"""
    now = datetime.utcnow()
    
    # Preserve original created_at, update updated_at
    return {
        "data": data,
        "metadata": {
            "created_at": existing_metadata.get("created_at", now.isoformat()),
            "updated_at": now.isoformat(),
            "source": source,
            "compute_id": compute_id,
            "ttl": ttl
        }
    }

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
        raise HTTPException(status_code=400, detail="table_type must be 'bright_uid' or 'account_id'")
    
    item = crud.get_item(identifier, category, table_type)
    if not item:
        metrics.increment_counter(f"{MetricNames.READ_SINGLE_ITEM}.not_found", tags={"identifier": identifier, "category": category, "table_type": table_type})
        raise HTTPException(status_code=404, detail="Item not found")
    metrics.increment_counter(f"{MetricNames.READ_SINGLE_ITEM}.success", tags={"identifier": identifier, "category": category, "table_type": table_type})
    return item


# 2) POST /get/item/{identifier} with body mapping → return mentioned features only
# Body: { "cat1": ["f1", "f2"], "cat2": ["f3"] }
@router.post("/get/item/{identifier}")
@time_function(MetricNames.READ_MULTI_CATEGORY)
def get_items_by_feature_mapping(identifier: str, mapping: Dict[str, List[str]], table_type: str = Query(default="bright_uid", description="Table type: 'bright_uid' or 'account_id'")):
    if table_type not in ["bright_uid", "account_id"]:
        raise HTTPException(status_code=400, detail="table_type must be 'bright_uid' or 'account_id'")
    
    if not mapping:
        metrics.increment_counter(f"{MetricNames.READ_MULTI_CATEGORY}.error", tags={"error_type": "empty_mapping", "table_type": table_type})
        raise HTTPException(status_code=400, detail="Mapping body cannot be empty")

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
        raise HTTPException(status_code=404, detail="No items found for provided mapping")

    metrics.increment_counter(f"{MetricNames.READ_MULTI_CATEGORY}.success", tags={"identifier": identifier, "table_type": table_type})
    return {"identifier": identifier, "table_type": table_type, "items": results, "missing_categories": missing}


# 3) POST /items/{identifier} write → replace entire features map per category
# Body: { "cat1": {...}, "cat2": {...} } (simple feature data)
# Metadata is auto-generated: new category gets fresh timestamps, existing preserves created_at
@router.post("/items/{identifier}")
@time_function(MetricNames.WRITE_MULTI_CATEGORY)
def upsert_items(identifier: str, items: Dict[str, Dict], table_type: str = Query(default="bright_uid", description="Table type: 'bright_uid' or 'account_id'")):
    if table_type not in ["bright_uid", "account_id"]:
        raise HTTPException(status_code=400, detail="table_type must be 'bright_uid' or 'account_id'")
    
    if not items:
        metrics.increment_counter(f"{MetricNames.WRITE_MULTI_CATEGORY}.error", tags={"error_type": "empty_body", "table_type": table_type})
        raise HTTPException(status_code=400, detail="Body cannot be empty")

    results: Dict[str, dict] = {}
    total_features = 0
    
    for category, features in items.items():
        if not isinstance(features, dict):
            raise HTTPException(status_code=400, detail=f"Features for category '{category}' must be an object")
        
        # Check if this is an update (item already exists)
        existing_item = crud.get_item(identifier, category, table_type)
        if existing_item and "features" in existing_item and "metadata" in existing_item["features"]:
            # This is an update - preserve the original created_at
            existing_metadata = existing_item["features"]["metadata"]
            features_obj = update_features_with_metadata(
                features, 
                existing_metadata, 
                source="api",
                compute_id=None,
                ttl=None
            )
        else:
            # This is a new item - create new metadata
            features_obj = create_features_with_metadata(
                features,
                source="api",
                compute_id=None,
                ttl=None
            )
        
        total_features += len(features)
        crud.put_item({table_type: identifier, "category": category, "features": features_obj}, table_type)
        results[category] = {"status": "replaced", "feature_count": len(features)}

    metrics.increment_counter(f"{MetricNames.WRITE_MULTI_CATEGORY}.success", tags={"identifier": identifier, "table_type": table_type, "categories_count": str(len(items))})
    return {"message": "Items written successfully (full replace per category)", "identifier": identifier, "table_type": table_type, "results": results, "total_features": total_features}
