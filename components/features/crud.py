from core.config import get_table
from core.metrics import metrics, time_function, MetricNames
from core.timestamp_utils import get_current_timestamp, ensure_timestamp_consistency
from core.logging_config import get_logger
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from decimal import Decimal
from datetime import datetime
from .models import FeatureMeta, Features

logger = get_logger("feature_crud")
deserializer = TypeDeserializer()
serializer = TypeSerializer()

def dynamodb_to_dict(dynamo_item: dict) -> dict:
    """
    Convert a DynamoDB JSON-like dict into a standard Python dict.
    Handles nested Maps and Decimals.
    """
    if not isinstance(dynamo_item, dict):
        return dynamo_item

    result = {}
    for k, v in dynamo_item.items():
        if isinstance(v, dict) and len(v) == 1 and list(v.keys())[0] in ["S", "N", "BOOL", "M", "L"]:
            # This is a DynamoDB-typed value → use deserializer
            result[k] = deserializer.deserialize(v)
        else:
            # Already a plain dict/Decimal → leave as is (or recurse)
            if isinstance(v, Decimal):
                result[k] = float(v)  # optional: convert Decimal → float
            elif isinstance(v, dict):
                result[k] = dynamodb_to_dict(v)
            else:
                result[k] = v
    return result


def _convert_floats_to_decimal(obj):
    """Convert float values to Decimal and datetime to string for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_floats_to_decimal(item) for item in obj]
    return obj


def dict_to_dynamodb(python_dict: dict) -> dict:
    """
    Convert a standard Python dict to DynamoDB format using TypeSerializer.
    This properly handles nested structures without excessive wrapping.
    Converts floats to Decimal for DynamoDB compatibility.
    """
    if not isinstance(python_dict, dict):
        return python_dict
    
    # Convert floats to Decimal (required by DynamoDB)
    converted_dict = _convert_floats_to_decimal(python_dict)
    
    # Use TypeSerializer to properly convert to DynamoDB format
    # It handles all nested structures correctly
    return serializer.serialize(converted_dict)


@time_function(MetricNames.DYNAMODB_GET_ITEM)
def get_item(identifier: str, category: str, table_type: str = "bright_uid"):
    """Get item from specified table type (bright_uid or account_pid)"""
    try:
        table = get_table(table_type)
        
        # Use appropriate partition key based on table type
        key = {table_type: identifier, "category": category}
        
        response = table.get_item(Key=key)
        item = response.get("Item")
        if not item:
            metrics.increment_counter(f"{MetricNames.DYNAMODB_GET_ITEM}.not_found", 
                                    tags={"category": category, "table_type": table_type})
            return None

        # Convert the features structure (data and meta)
        if "features" in item:
            features = dynamodb_to_dict(item["features"])
            item["features"] = features

        metrics.increment_counter(f"{MetricNames.DYNAMODB_GET_ITEM}.found", 
                                tags={"category": category, "table_type": table_type})
        return item
        
    except Exception as e:
        # Log the error and record metrics
        error_type = type(e).__name__
        metrics.increment_counter(f"{MetricNames.DYNAMODB_GET_ITEM}.error", 
                                tags={"category": category, "table_type": table_type, "error_type": error_type})
        
        # Re-raise the exception to be handled by the calling function
        raise


@time_function(MetricNames.DYNAMODB_PUT_ITEM)
def put_item(item_data: dict, table_type: str = "bright_uid"):
    """Put a single item to DynamoDB. boto3 Table resource handles serialization automatically."""
    try:
        table = get_table(table_type)
        
        # Convert floats to Decimal for boto3 compatibility
        # Table resource will handle DynamoDB format conversion automatically
        if "features" in item_data:
            item_data["features"] = _convert_floats_to_decimal(item_data["features"])
        
        response = table.put_item(Item=item_data)
        
        # Record metrics
        category = item_data.get("category", "unknown")
        features = item_data.get("features", {})
        feature_count = len(features.get("data", {})) if isinstance(features, dict) else 0
        metrics.increment_counter(f"{MetricNames.DYNAMODB_PUT_ITEM}.success", 
                                tags={"category": category, "table_type": table_type})
        metrics.gauge(f"{MetricNames.DYNAMODB_PUT_ITEM}.feature_count", 
                     feature_count, tags={"category": category, "table_type": table_type})
        
        return response
        
    except Exception as e:
        # Log the error and record metrics
        error_type = type(e).__name__
        category = item_data.get("category", "unknown") if item_data else "unknown"
        metrics.increment_counter(f"{MetricNames.DYNAMODB_PUT_ITEM}.error", 
                                tags={"category": category, "table_type": table_type, "error_type": error_type})
        
        # Re-raise the exception to be handled by the calling function
        raise


@time_function(MetricNames.DYNAMODB_UPDATE_ITEM)
def upsert_item_with_meta(identifier: str, category: str, features_data: dict, table_type: str = "bright_uid", compute_id: str = None):
    """Upsert item with automatic meta handling - preserves created_at, updates updated_at, and stores compute_id."""
    try:
        table = get_table(table_type)
        
        # Use appropriate partition key based on table type
        key = {table_type: identifier, "category": category}
        
        # Check if item exists to preserve created_at
        existing_item = table.get_item(Key=key).get("Item")
        
        # Create the features object with meta using centralized timestamp utility
        now = get_current_timestamp()
        
        # Preserve created_at if item exists, otherwise use current time
        if existing_item and "features" in existing_item:
            existing_features = dynamodb_to_dict(existing_item["features"])
            existing_created_at = existing_features.get("meta", {}).get("created_at")
            # Ensure timestamp consistency for existing created_at
            created_at = ensure_timestamp_consistency(existing_created_at) if existing_created_at else now
        else:
            created_at = now
        
        meta = FeatureMeta(
            created_at=created_at,
            updated_at=now,
            compute_id=compute_id
        )
        features_obj = Features(
            data=features_data,
            meta=meta
        )
        
        # Convert to plain dict
        features_dict = features_obj.model_dump()
        
        # Convert floats to Decimal for boto3 compatibility (Table resource requires this)
        # But don't use dict_to_dynamodb() as it manually serializes to DynamoDB format
        # The Table resource will handle the DynamoDB format conversion
        features_dict = _convert_floats_to_decimal(features_dict)
        
        # Use PutItem to replace the entire features object
        item_data = {**key, "features": features_dict}
        table.put_item(Item=item_data)
        
        # Convert back to regular dict for response
        item = item_data.copy()
        if "features" in item:
            item["features"] = dynamodb_to_dict(item["features"])
        
        # Record metrics
        feature_count = len(features_data)
        metrics.increment_counter(f"{MetricNames.DYNAMODB_UPDATE_ITEM}.success", 
                                tags={"category": category, "table_type": table_type})
        metrics.gauge(f"{MetricNames.DYNAMODB_UPDATE_ITEM}.feature_count", 
                     feature_count, tags={"category": category, "table_type": table_type})
        
        return item
        
    except Exception as e:
        # Log the error and record metrics
        error_type = type(e).__name__
        metrics.increment_counter(f"{MetricNames.DYNAMODB_UPDATE_ITEM}.error", 
                                tags={"category": category, "table_type": table_type, "error_type": error_type})
        
        # Re-raise the exception to be handled by the calling function
        raise
