from .config import TABLES
from .utils import dynamodb_to_dict, dict_to_dynamodb
from .metrics import metrics, time_function, MetricNames

@time_function(MetricNames.DYNAMODB_GET_ITEM)
def get_item(identifier: str, category: str, table_type: str = "bright_uid"):
    """Get item from specified table type (bright_uid or account_id)"""
    table = TABLES.get(table_type)
    if not table:
        raise ValueError(f"Invalid table_type: {table_type}. Must be 'bright_uid' or 'account_id'")
    
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


@time_function(MetricNames.DYNAMODB_PUT_ITEM)
def put_item(item_data: dict, table_type: str = "bright_uid"):
    """Put a single item to DynamoDB. Converts features dict to DynamoDB format."""
    table = TABLES.get(table_type)
    if not table:
        raise ValueError(f"Invalid table_type: {table_type}. Must be 'bright_uid' or 'account_id'")
    
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


@time_function(MetricNames.DYNAMODB_UPDATE_ITEM)
def update_item_features(identifier: str, category: str, features: dict, table_type: str = "bright_uid"):
    """Update features for an existing item. Merges with existing features."""
    table = TABLES.get(table_type)
    if not table:
        raise ValueError(f"Invalid table_type: {table_type}. Must be 'bright_uid' or 'account_id'")
    
    # Convert features to DynamoDB format
    dynamo_features = dict_to_dynamodb(features)
    
    # Use appropriate partition key based on table type
    key = {table_type: identifier, "category": category}
    
    # Use update_item with SET to merge features
    response = table.update_item(
        Key=key,
        UpdateExpression="SET features = :features",
        ExpressionAttributeValues={":features": dynamo_features},
        ReturnValues="ALL_NEW"
    )
    
    # Convert back to regular dict for response
    item = response.get("Attributes", {})
    if "features" in item:
        item["features"] = dynamodb_to_dict(item["features"])
    
    # Record metrics
    feature_count = len(features)
    metrics.increment_counter(f"{MetricNames.DYNAMODB_UPDATE_ITEM}.success", 
                            tags={"category": category, "table_type": table_type})
    metrics.gauge(f"{MetricNames.DYNAMODB_UPDATE_ITEM}.feature_count", 
                 feature_count, tags={"category": category, "table_type": table_type})
    
    return item
