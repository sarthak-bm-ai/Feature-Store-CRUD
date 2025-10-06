from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from decimal import Decimal

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


def filter_features(item: dict, feature_keys: set[str]) -> dict:
    """
    Return a shallow copy of `item` where `features` map contains only the
    requested keys. If a key does not exist, it is ignored.
    """
    if not feature_keys:
        return item
    filtered = dict(item)
    features = filtered.get("features") or {}
    if isinstance(features, dict):
        filtered["features"] = {k: v for k, v in features.items() if k in feature_keys}
    return filtered


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

