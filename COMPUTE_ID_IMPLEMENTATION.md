# Compute ID Implementation

**Date**: October 16, 2025  
**Feature**: Pass `compute_id` from request metadata through the write pipeline and store it in feature metadata

---

## Table of Contents

1. [Overview](#overview)
2. [Implementation Details](#implementation-details)
3. [Changes Summary](#changes-summary)
4. [Request/Response Flow](#requestresponse-flow)
5. [Example Usage](#example-usage)
6. [Testing](#testing)
7. [Benefits](#benefits)

---

## Overview

The `compute_id` field is now accepted in the `WriteRequestMeta` and passed through the entire write pipeline (controller → flow → crud) to be stored in the feature metadata. This allows tracking which compute job generated specific features, similar to how we track the `source` field.

### Key Design Principles

1. **Optional Field**: `compute_id` is optional - if not provided, it will be stored as `None`
2. **Metadata-Level**: `compute_id` is part of the request metadata (alongside `source`), not the data payload
3. **Automatic Storage**: No business logic changes needed - the field is automatically passed through and stored
4. **Backward Compatible**: Existing requests without `compute_id` will continue to work

---

## Implementation Details

### 1. Model Layer (`components/features/models.py`)

#### Updated `WriteRequestMeta`

```python
class WriteRequestMeta(BaseModel):
    source: str = Field(..., description="Source of the request", example="prediction_service")
    compute_id: Optional[str] = Field(None, description="ID of the compute job that generated the features")
    
    @validator('source')
    def validate_source(cls, v):
        if v != "prediction_service":
            raise ValueError('Only prediction_service is allowed for write operations')
        return v
```

**Changes**:
- Added `compute_id` as an optional string field
- Default value is `None` if not provided
- No validation on `compute_id` - any string value is accepted

#### `FeatureMeta` (Already Existed)

```python
class FeatureMeta(BaseModel):
    created_at: datetime = Field(..., description="Creation timestamp in ISO 8601 format")
    updated_at: datetime = Field(..., description="Last update timestamp in ISO 8601 format")
    compute_id: Optional[str] = Field(None, description="ID of the compute job that generated the features")
```

**Note**: `FeatureMeta` already had `compute_id` field, but it was being hardcoded to `"None"` string in the CRUD layer.

---

### 2. Controller Layer (`components/features/controller.py`)

#### Updated `upsert_category` Method

```python
@staticmethod
def upsert_category(request_data: Dict) -> Dict:
    """
    Controller for upserting a single category's features.
    
    Args:
        request_data: Request containing meta and data with entity info, category, and features
        
    Returns:
        Dict containing operation results
    """
    logger.info("Controller: Upserting single category from request data")
    
    # Extract metadata (compute_id)
    meta = request_data.get("meta", {})
    compute_id = meta.get("compute_id")  # ← NEW: Extract compute_id from meta
    
    # Extract data (Pydantic already validated structure)
    data = request_data["data"]
    entity_type = data["entity_type"]
    entity_value = data["entity_value"]
    category = data["category"]
    features = data["features"]
    
    # Validate single category write (business rules: category whitelist, non-empty features)
    FeatureServices.validate_single_category_write(category, features)
    
    # Execute flow with compute_id
    return FeatureFlows.upsert_category_flow(entity_value, category, features, entity_type, compute_id)
    #                                                                                       ^^^^^^^^^^^ NEW
```

**Changes**:
- Extract `compute_id` from `request_data["meta"]`
- Pass `compute_id` as the 5th parameter to `upsert_category_flow`

---

### 3. Flow Layer (`components/features/flows.py`)

#### Updated `upsert_category_flow` Method

```python
@staticmethod
def upsert_category_flow(entity_value: str, category: str, features: Dict[str, Any], 
                        entity_type: str, compute_id: Optional[str] = None) -> Dict:
    #                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ NEW parameter
    """
    Flow for upserting a single category's features with automatic meta handling.
    
    Args:
        entity_value: User/account identifier
        category: Feature category
        features: Features data dictionary
        entity_type: Entity type (bright_uid or account_pid)
        compute_id: Optional ID of the compute job that generated the features  # ← NEW
        
    Returns:
        Dict containing operation results
        
    Raises:
        ValueError: If validation fails
    """
    logger.info(f"Upserting category '{category}' for: {entity_value} to {entity_type} with compute_id: {compute_id}")
    
    if not features:
        logger.error("Empty features provided")
        metrics.increment_counter(
            f"{MetricNames.WRITE_SINGLE_CATEGORY}.error",
            tags={"error_type": "empty_features", "entity_type": entity_type, "category": category}
        )
        raise ValueError("Features cannot be empty")
    
    # Upsert with automatic meta handling, including compute_id
    crud.upsert_item_with_meta(entity_value, category, features, entity_type, compute_id)
    #                                                                          ^^^^^^^^^^^ NEW
    
    # ... Kafka publishing logic ...
    
    return {
        "message": "Category written successfully (full replace)",
        "entity_value": entity_value,
        "entity_type": entity_type,
        "category": category,
        "feature_count": feature_count
    }
```

**Changes**:
- Added `compute_id: Optional[str] = None` parameter
- Updated docstring to document the new parameter
- Pass `compute_id` to `crud.upsert_item_with_meta`
- Enhanced logging to include `compute_id`

---

### 4. CRUD Layer (`components/features/crud.py`)

#### Updated `upsert_item_with_meta` Function

```python
@time_function(MetricNames.DYNAMODB_UPDATE_ITEM)
def upsert_item_with_meta(identifier: str, category: str, features_data: dict, 
                         table_type: str = "bright_uid", compute_id: str = None):
    #                                                    ^^^^^^^^^^^^^^^^^^^^^ NEW parameter
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
            created_at = ensure_timestamp_consistency(existing_created_at) if existing_created_at else now
        else:
            created_at = now
        
        meta = FeatureMeta(
            created_at=created_at,
            updated_at=now,
            compute_id=compute_id  # ← CHANGED: Use provided compute_id instead of hardcoded "None"
        )
        features_obj = Features(
            data=features_data,
            meta=meta
        )
        
        # ... rest of the function ...
```

**Changes**:
- Added `compute_id: str = None` parameter
- Changed `compute_id="None"` to `compute_id=compute_id` in `FeatureMeta` instantiation
- Updated docstring to mention `compute_id` storage

---

## Changes Summary

### Files Modified

| File | Changes |
|------|---------|
| `components/features/models.py` | Added `compute_id` field to `WriteRequestMeta` |
| `components/features/controller.py` | Extract `compute_id` from meta and pass to flow |
| `components/features/flows.py` | Accept `compute_id` parameter and pass to crud |
| `components/features/crud.py` | Accept `compute_id` parameter and store in `FeatureMeta` |
| `test/conftest.py` | Updated fixtures to include `compute_id` in test data |
| `test/test_models.py` | Added test for `WriteRequestMeta` with `compute_id` |
| `test/test_controller.py` | Updated test to pass `compute_id` to flow |
| `test/test_flows.py` | Updated tests to pass `compute_id` to crud |
| `test/test_routes.py` | Updated route tests to include `compute_id` in requests |

### Lines Changed

- **Models**: +1 line (add `compute_id` field)
- **Controller**: +4 lines (extract and pass `compute_id`)
- **Flows**: +2 lines (add parameter, pass to crud)
- **CRUD**: +1 line (use provided `compute_id`)
- **Tests**: ~15 lines (update test data and assertions)

**Total**: ~23 lines changed/added

---

## Request/Response Flow

### Write Request Flow

```
Client Request
    ↓
┌──────────────────────────────────────────────────┐
│ POST /api/v1/items                               │
│ {                                                │
│   "meta": {                                      │
│     "source": "prediction_service",              │
│     "compute_id": "spark-job-2025-10-16-abc123" │ ← Provided by client
│   },                                             │
│   "data": {                                      │
│     "entity_type": "bright_uid",                 │
│     "entity_value": "user-123",                  │
│     "category": "d0_unauth_features",            │
│     "features": {"credit_score": 750}            │
│   }                                              │
│ }                                                │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ FastAPI Route (routes.py)                        │
│ - Validates request with Pydantic                │
│ - Calls FeatureController.upsert_category()      │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ Controller (controller.py)                       │
│ - Extracts compute_id from meta                  │
│ - Validates category whitelist                   │
│ - Calls FeatureFlows.upsert_category_flow()      │
│   with compute_id parameter                      │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ Flow (flows.py)                                  │
│ - Validates features not empty                   │
│ - Calls crud.upsert_item_with_meta()             │
│   with compute_id parameter                      │
│ - Publishes Kafka event                          │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ CRUD (crud.py)                                   │
│ - Preserves created_at if item exists            │
│ - Sets updated_at to current time                │
│ - Sets compute_id to provided value              │
│ - Writes to DynamoDB                             │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ DynamoDB Storage                                 │
│ {                                                │
│   "bright_uid": "user-123",                      │
│   "category": "d0_unauth_features",              │
│   "features": {                                  │
│     "data": {"credit_score": 750},               │
│     "meta": {                                    │
│       "created_at": "2025-10-16T10:00:00.000Z",  │
│       "updated_at": "2025-10-16T10:00:00.000Z",  │
│       "compute_id": "spark-job-2025-10-16-abc123" │ ← Stored!
│     }                                            │
│   }                                              │
│ }                                                │
└──────────────────────────────────────────────────┘
```

### Read Request Flow

When reading features, the stored `compute_id` is returned in the metadata:

```
Client Request
    ↓
GET /api/v1/get/item/user-123?category=d0_unauth_features
    ↓
Response:
{
  "bright_uid": "user-123",
  "category": "d0_unauth_features",
  "features": {
    "data": {"credit_score": 750},
    "meta": {
      "created_at": "2025-10-16T10:00:00.000Z",
      "updated_at": "2025-10-16T10:00:00.000Z",
      "compute_id": "spark-job-2025-10-16-abc123"  ← Returned to client
    }
  }
}
```

---

## Example Usage

### Example 1: Write with compute_id

```bash
curl -X POST http://localhost:8015/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service",
      "compute_id": "spark-job-2025-10-16-abc123"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "user-12345",
      "category": "d0_unauth_features",
      "features": {
        "credit_score": 750,
        "debt_to_income_ratio": 0.35,
        "payment_history_score": 85.5
      }
    }
  }'
```

**Response**:
```json
{
  "message": "Category written successfully (full replace)",
  "entity_value": "user-12345",
  "entity_type": "bright_uid",
  "category": "d0_unauth_features",
  "feature_count": 3
}
```

### Example 2: Write without compute_id (backward compatible)

```bash
curl -X POST http://localhost:8015/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "user-12345",
      "category": "d0_unauth_features",
      "features": {
        "credit_score": 780
      }
    }
  }'
```

**Stored metadata**:
```json
{
  "meta": {
    "created_at": "2025-10-16T10:05:00.000Z",
    "updated_at": "2025-10-16T10:05:00.000Z",
    "compute_id": null
  }
}
```

### Example 3: Read features with compute_id

```bash
curl -X GET "http://localhost:8015/api/v1/get/item/user-12345?category=d0_unauth_features&entity_type=bright_uid"
```

**Response**:
```json
{
  "bright_uid": "user-12345",
  "category": "d0_unauth_features",
  "features": {
    "data": {
      "credit_score": 750,
      "debt_to_income_ratio": 0.35,
      "payment_history_score": 85.5
    },
    "meta": {
      "created_at": "2025-10-16T10:00:00.000Z",
      "updated_at": "2025-10-16T10:00:00.000Z",
      "compute_id": "spark-job-2025-10-16-abc123"
    }
  }
}
```

---

## Testing

### Test Coverage

All tests pass successfully (139 tests):

```bash
cd /Users/sarhakjain/Feature-Store-CRUD/Feature-Store-CRUD
source venv/bin/activate
python -m pytest test/ -v
```

#### New/Updated Tests

1. **`test_models.py`**:
   - `test_write_request_meta_with_compute_id`: Tests `WriteRequestMeta` accepts `compute_id`
   - Updated existing tests to verify default `None` value

2. **`test_controller.py`**:
   - Updated `test_upsert_category_success` to pass `compute_id` to flow
   - Verified controller extracts and passes `compute_id` correctly

3. **`test_flows.py`**:
   - Updated all `upsert_category_flow` calls to include `compute_id` parameter
   - Tests with `compute_id="test-compute-123"` and `compute_id=None`

4. **`test_routes.py`**:
   - Updated write request payloads to include `compute_id`
   - Verified end-to-end flow works with `compute_id`

5. **`conftest.py`**:
   - Updated `sample_write_request` fixture to include `compute_id`
   - Updated `sample_dynamodb_item` fixture to reflect stored `compute_id`

### Test Scenarios Covered

| Scenario | Test File | Status |
|----------|-----------|--------|
| Write with `compute_id` provided | `test_routes.py`, `test_controller.py` | ✅ Pass |
| Write without `compute_id` (None) | `test_flows.py` | ✅ Pass |
| Read features returns `compute_id` | `test_crud.py` | ✅ Pass |
| Pydantic validation of `compute_id` | `test_models.py` | ✅ Pass |
| Controller passes `compute_id` to flow | `test_controller.py` | ✅ Pass |
| Flow passes `compute_id` to crud | `test_flows.py` | ✅ Pass |
| CRUD stores `compute_id` in metadata | `test_crud.py` | ✅ Pass |

---

## Benefits

### 1. **Traceability**

- Track which compute job generated specific features
- Debug feature quality issues by identifying the source compute job
- Audit trail for feature lineage

**Example Use Case**:
```
User reports incorrect credit score → 
Check compute_id in metadata → 
Identify problematic Spark job → 
Investigate and fix the job
```

### 2. **Operational Monitoring**

- Monitor feature freshness per compute job
- Detect stale features from old compute jobs
- Alert when specific compute jobs fail to update features

**Example Query**:
```sql
-- Find all features generated by a specific compute job
SELECT * FROM features 
WHERE features.meta.compute_id = 'spark-job-2025-10-16-abc123'
```

### 3. **Data Quality**

- Compare feature values across different compute jobs
- A/B test different feature computation algorithms
- Roll back to previous compute job if new one produces bad features

### 4. **Compliance & Auditing**

- Meet regulatory requirements for data lineage
- Prove which system generated which features
- Support data governance initiatives

### 5. **Backward Compatibility**

- Existing clients without `compute_id` continue to work
- Gradual rollout - add `compute_id` only when needed
- No breaking changes to existing APIs

---

## Implementation Notes

### Design Decisions

1. **Optional Field**: Made `compute_id` optional to maintain backward compatibility
   - Old clients don't need to change
   - New clients can start using it immediately

2. **Metadata-Level**: Placed in `meta` instead of `data`
   - Separates business data from operational metadata
   - Consistent with `source` field placement
   - Doesn't pollute feature data

3. **No Validation**: Accept any string value for `compute_id`
   - Flexible for different compute systems (Spark, Airflow, etc.)
   - No coupling to specific compute job ID formats
   - Client decides the format

4. **Pass-Through Pattern**: Simple data flow without transformation
   - No business logic needed
   - Easy to understand and maintain
   - Minimal code changes

### Alternative Approaches Considered

#### ❌ **Hardcode compute_id in service layer**
```python
# BAD: Compute ID should come from the client/compute job
compute_id = f"job-{datetime.now().isoformat()}"
```
**Why rejected**: Client (compute job) knows its own ID, not the API

#### ❌ **Store compute_id in top-level item**
```python
{
  "bright_uid": "user-123",
  "category": "d0_unauth_features",
  "compute_id": "spark-job-123",  # ← BAD: Pollutes item structure
  "features": {...}
}
```
**Why rejected**: Mixes operational metadata with feature data

#### ✅ **Current approach: Pass from request meta to feature meta**
```python
Request meta → Controller → Flow → CRUD → Feature meta
```
**Why chosen**: Clean separation, backward compatible, traceable

---

## Future Enhancements

### 1. Compute ID Validation

Add optional validation for compute job ID format:

```python
@validator('compute_id')
def validate_compute_id(cls, v):
    if v and not re.match(r'^[a-z]+-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+$', v):
        raise ValueError('compute_id must match format: job-type-YYYY-MM-DD-id')
    return v
```

### 2. Compute Job Metadata API

Create endpoint to query features by compute_id:

```python
GET /api/v1/features/by-compute-id/{compute_id}
```

### 3. Compute Job Analytics

Add metrics tracking:
- Features per compute job
- Compute job success/failure rates
- Average time between compute job runs

### 4. Compute Job History

Store historical compute_ids to track feature updates:

```python
{
  "meta": {
    "created_at": "...",
    "updated_at": "...",
    "compute_id": "current-job-id",
    "compute_history": [
      {"compute_id": "job-1", "timestamp": "..."},
      {"compute_id": "job-2", "timestamp": "..."}
    ]
  }
}
```

---

## Summary

The `compute_id` implementation provides a clean, backward-compatible way to track feature lineage from compute jobs to stored features. The implementation follows the existing pattern of the `source` field, requiring minimal code changes (~23 lines) while providing significant operational and data quality benefits.

**Key Takeaways**:
- ✅ Optional field (backward compatible)
- ✅ Metadata-level (clean separation)
- ✅ Pass-through pattern (simple, maintainable)
- ✅ Fully tested (139 tests passing)
- ✅ Production-ready (no breaking changes)


