# Single Category Write Refactoring

**Date**: October 16, 2025  
**Status**: ✅ Complete  
**Tests**: 118/118 passing (100%)

---

## Summary

Refactored the write API (POST `/items`) to only accept **single category writes** instead of multiple categories. This simplifies the API, reduces complexity, and aligns with the actual usage pattern.

---

## What Changed

### Before (Multi-Category Write)
```json
POST /api/v1/items
{
  "meta": {"source": "prediction_service"},
  "data": {
    "entity_type": "bright_uid",
    "entity_value": "user123",
    "feature_list": [
      {
        "category": "d0_unauth_features",
        "features": {"credit_score": 750}
      },
      {
        "category": "ncr_unauth_features",
        "features": {"transactions": 10}
      }
    ]
  }
}
```

### After (Single-Category Write)
```json
POST /api/v1/items
{
  "meta": {"source": "prediction_service"},
  "data": {
    "entity_type": "bright_uid",
    "entity_value": "user123",
    "category": "d0_unauth_features",
    "features": {"credit_score": 750}
  }
}
```

---

## Response Format Changed

### Before
```json
{
  "message": "Items written successfully (full replace per category)",
  "entity_value": "user123",
  "entity_type": "bright_uid",
  "results": {
    "d0_unauth_features": {"status": "replaced", "feature_count": 1},
    "ncr_unauth_features": {"status": "replaced", "feature_count": 1}
  },
  "total_features": 2
}
```

### After
```json
{
  "message": "Category written successfully (full replace)",
  "entity_value": "user123",
  "entity_type": "bright_uid",
  "category": "d0_unauth_features",
  "feature_count": 1
}
```

---

## Code Changes

### 1. Models (`components/features/models.py`)

**Before**:
```python
class WriteRequest(BaseModel):
    meta: WriteRequestMeta
    data: Dict[str, Any]
    
    @validator('data')
    def validate_data(cls, v):
        required_fields = ['entity_type', 'entity_value', 'feature_list']
        # feature_list must be a non-empty list
```

**After**:
```python
class WriteRequest(BaseModel):
    meta: WriteRequestMeta
    data: Dict[str, Any]
    
    @validator('data')
    def validate_data(cls, v):
        required_fields = ['entity_type', 'entity_value', 'category', 'features']
        # category must be a non-empty string
        # features must be a non-empty dictionary
```

**WriteResponse Before**:
```python
class WriteResponse(BaseModel):
    message: str
    entity_value: str
    entity_type: str
    results: Dict[str, Dict[str, Any]]  # Multiple categories
    total_features: int
```

**WriteResponse After**:
```python
class WriteResponse(BaseModel):
    message: str
    entity_value: str
    entity_type: str
    category: str       # Single category
    feature_count: int  # Feature count for this category
```

---

### 2. Services (`components/features/services.py`)

**Removed**:
- `convert_feature_list_to_items()` - No longer needed for list of categories

**Added**:
```python
@staticmethod
def validate_single_category_write(category: str, features: Dict[str, Any]) -> None:
    """
    Validate single category write operation.
    - Validates category is a string
    - Validates features is a non-empty dict
    - Validates category is in whitelist
    """
```

---

### 3. Controller (`components/features/controller.py`)

**Before**: `upsert_features()`
- Extracted `feature_list` from request
- Converted `feature_list` to `items` dict
- Validated items
- Called flow with items dict

**After**: `upsert_category()`
```python
@staticmethod
def upsert_category(request_data: Dict) -> Dict:
    """Controller for upserting a single category's features."""
    data = request_data["data"]
    entity_type = data["entity_type"]
    entity_value = data["entity_value"]
    category = data["category"]       # Direct access
    features = data["features"]        # Direct access
    
    # Validate single category write
    FeatureServices.validate_single_category_write(category, features)
    
    # Execute flow
    return FeatureFlows.upsert_category_flow(entity_value, category, features, entity_type)
```

---

### 4. Flows (`components/features/flows.py`)

**Before**: `upsert_features_flow(entity_value, items, entity_type)`
- Looped through `items` dict (multiple categories)
- Processed each category
- Built results dict
- Returned aggregated results

**After**: `upsert_category_flow(entity_value, category, features, entity_type)`
```python
@staticmethod
def upsert_category_flow(entity_value: str, category: str, features: Dict[str, Any], entity_type: str) -> Dict:
    """Flow for upserting a single category's features."""
    # Validate features not empty
    if not features:
        raise ValueError("Features cannot be empty")
    
    # Upsert with automatic meta handling
    crud.upsert_item_with_meta(entity_value, category, features, entity_type)
    
    # Publish Kafka event (with error handling)
    publish_feature_availability_event(...)
    
    # Record metrics
    metrics.increment_counter(MetricNames.WRITE_SINGLE_CATEGORY.success, ...)
    
    # Return simplified response
    return {
        "message": "Category written successfully (full replace)",
        "entity_value": entity_value,
        "entity_type": entity_type,
        "category": category,
        "feature_count": len(features)
    }
```

---

### 5. Routes (`api/v1/routes.py`)

**Before**:
```python
@router.post("/items", response_model=WriteResponseSchema)
@time_function(MetricNames.WRITE_MULTI_CATEGORY)
def upsert_items(request_data: WriteRequestSchema):
    """Write/update features with automatic metadata handling."""
    return FeatureController.upsert_features(request_data.dict())
```

**After**:
```python
@router.post("/items", response_model=WriteResponseSchema)
@time_function(MetricNames.WRITE_SINGLE_CATEGORY)
def upsert_category(request_data: WriteRequestSchema):
    """Write/update a single category's features with automatic metadata handling."""
    return FeatureController.upsert_category(request_data.dict())
```

---

### 6. Metrics (`core/metrics.py`)

**Added**:
```python
class MetricNames:
    # Write operations
    WRITE_SINGLE_CATEGORY = "write.single_category"  # New metric for single category writes
    WRITE_MULTI_CATEGORY = "write.multi_category"    # Deprecated
```

---

## Tests Updated

### Test Files Modified:
1. **`test/test_controller.py`**: 
   - Renamed `TestUpsertFeaturesController` → `TestUpsertCategoryController`
   - Updated request data format (no `feature_list`, direct `category` and `features`)
   - Updated expected response format

2. **`test/test_flows.py`**: 
   - Renamed `TestUpsertFeaturesFlow` → `TestUpsertCategoryFlow`
   - Removed test for multiple categories
   - Updated test calls to use `upsert_category_flow(entity_value, category, features, entity_type)`

3. **`test/test_models.py`**: 
   - Updated `TestWriteRequest` to use new format
   - Updated `TestWriteResponse` to use new format

4. **`test/test_routes.py`**: 
   - Renamed `TestUpsertItemsEndpoint` → `TestUpsertCategoryEndpoint`
   - Updated request payloads
   - Updated mock patches

5. **`test/conftest.py`**: 
   - Updated `sample_write_request` fixture

**Test Results**: ✅ 118/118 tests passing

---

## Benefits

### 1. **Simplicity**
- Simpler request structure
- No need to loop through categories
- Direct access to category and features

### 2. **Clearer API Contract**
- One write = one category
- Makes it explicit that each write replaces the entire category
- Easier for API consumers to understand

### 3. **Better Error Handling**
- Single category validation is straightforward
- No ambiguity about partial failures

### 4. **Reduced Complexity**
- Removed `convert_feature_list_to_items()` function
- Removed `validate_items()` (replaced with `validate_single_category_write()`)
- Simpler flow logic without loops

### 5. **Performance**
- One DB call per API request (was always the case, but now explicit)
- One Kafka event per API request
- Simpler metrics tracking

---

## Migration Guide

### For API Consumers

**Before** (Multiple Categories):
```bash
curl -X POST http://localhost:8000/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"source": "prediction_service"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "user123",
      "feature_list": [
        {"category": "d0_unauth_features", "features": {"credit_score": 750}},
        {"category": "ncr_unauth_features", "features": {"transactions": 10}}
      ]
    }
  }'
```

**After** (Single Category - Make 2 Requests):
```bash
# Request 1
curl -X POST http://localhost:8000/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"source": "prediction_service"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "user123",
      "category": "d0_unauth_features",
      "features": {"credit_score": 750}
    }
  }'

# Request 2
curl -X POST http://localhost:8000/api/v1/items \
  -H "Content-Type": application/json" \
  -d '{
    "meta": {"source": "prediction_service"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "user123",
      "category": "ncr_unauth_features",
      "features": {"transactions": 10}
    }
  }'
```

---

## Naming Conventions Updated

| Component | Old Name | New Name |
|-----------|----------|----------|
| Controller Method | `upsert_features` | `upsert_category` |
| Flow Method | `upsert_features_flow` | `upsert_category_flow` |
| Service Method | `convert_feature_list_to_items` | ~~Removed~~ |
| Service Method | `validate_items` | `validate_single_category_write` |
| Route Function | `upsert_items` | `upsert_category` |
| Metric Name | `WRITE_MULTI_CATEGORY` | `WRITE_SINGLE_CATEGORY` |
| Test Class | `TestUpsertFeaturesController` | `TestUpsertCategoryController` |
| Test Class | `TestUpsertFeaturesFlow` | `TestUpsertCategoryFlow` |
| Test Class | `TestUpsertItemsEndpoint` | `TestUpsertCategoryEndpoint` |

---

## Documentation Updated

- ✅ `SINGLE_CATEGORY_WRITE_REFACTORING.md` (this file)
- ⏳ `README.md` - API examples need updating
- ⏳ `API_DOCUMENTATION.md` - Endpoint docs need updating
- ⏳ `POSTMAN_TESTING_CURLS.md` - Test curls need updating

---

## Summary

✅ **Refactoring Complete**: Single category write API is now live  
✅ **All Tests Passing**: 118/118 tests pass  
✅ **Simplified Codebase**: Removed multi-category logic loops and conversion functions  
✅ **Clearer API Contract**: One write = one category replacement  
✅ **Better Naming**: Method names reflect single-category nature  

**Next Step**: Update remaining documentation files to reflect the new API structure.

