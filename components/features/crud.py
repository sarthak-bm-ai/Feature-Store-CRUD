from core.config import get_table
from core.metrics import metrics, time_function, MetricNames
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from decimal import Decimal
from datetime import datetime
from .models import FeatureMetadata, Features

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


def dict_to_dynamodb(python_dict: dict) -> dict:
    """
    Convert a standard Python dict to DynamoDB format.
    Handles nested dicts and converts them to DynamoDB Maps.
    """
    if not isinstance(python_dict, dict):
        return python_dict
    
    result = {}
    for k, v in python_dict.items():
        if isinstance(v, dict):
            result[k] = {"M": dict_to_dynamodb(v)}
        elif isinstance(v, str):
            result[k] = {"S": v}
        elif isinstance(v, (int, float)):
            result[k] = {"N": str(v)}
        elif isinstance(v, bool):
            result[k] = {"BOOL": v}
        elif isinstance(v, list):
            result[k] = {"L": [{"S": str(item)} if isinstance(item, str) else {"N": str(item)} if isinstance(item, (int, float)) else {"BOOL": item} if isinstance(item, bool) else {"S": str(item)} for item in v]}
        else:
            result[k] = {"S": str(v)}
    return result


@time_function(MetricNames.DYNAMODB_GET_ITEM)
def get_item(identifier: str, category: str, table_type: str = "bright_uid"):
    """Get item from specified table type (bright_uid or account_id)"""
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

        # Convert the features structure (data and metadata)
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
    """Put a single item to DynamoDB. Converts features dict to DynamoDB format."""
    try:
        table = get_table(table_type)
        
        # Convert features dict to DynamoDB format
        if "features" in item_data:
            item_data["features"] = dict_to_dynamodb(item_data["features"])
        
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
def upsert_item_with_metadata(identifier: str, category: str, features_data: dict, table_type: str = "bright_uid"):
    """Upsert item with automatic metadata handling - preserves created_at, updates updated_at."""
    try:
        table = get_table(table_type)
        
        # Use appropriate partition key based on table type
        key = {table_type: identifier, "category": category}
        
        # Check if item exists to preserve created_at
        existing_item = table.get_item(Key=key).get("Item")
        
        # Create the features object with metadata
        now = datetime.utcnow().isoformat()
        
        # Preserve created_at if item exists, otherwise use current time
        if existing_item and "features" in existing_item:
            existing_features = dynamodb_to_dict(existing_item["features"])
            created_at = existing_features.get("metadata", {}).get("created_at", now)
        else:
            created_at = now
        
        metadata = FeatureMetadata(
            created_at=created_at,
            updated_at=now,
            compute_id="None"
        )
        features_obj = Features(
            data=features_data,
            metadata=metadata
        )
        
        # Convert to DynamoDB format
        dynamo_features = dict_to_dynamodb(features_obj.dict())
        
        # Use PutItem to replace the entire features object
        item_data = {**key, "features": dynamo_features}
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
