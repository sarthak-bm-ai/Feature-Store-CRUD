# Metadata Behavior Documentation

## Overview
The Feature Store API properly handles `created_at` and `updated_at` timestamps to ensure data integrity and audit trails.

## Key Behaviors

### 1. New Item Creation
When creating a new item (category doesn't exist):
- **`created_at`**: Set to current timestamp
- **`updated_at`**: Set to current timestamp (same as created_at)

### 2. Existing Item Update
When updating an existing item (category already exists):
- **`created_at`**: **PRESERVED** from original creation
- **`updated_at`**: **UPDATED** to current timestamp

### 3. New Category for Existing User
When adding a new category to an existing user:
- **`created_at`**: Set to current timestamp (fresh creation)
- **`updated_at`**: Set to current timestamp (same as created_at)

## Implementation Details

### Helper Functions

#### `create_features_with_metadata()`
Used for **NEW** items:
```python
def create_features_with_metadata(data: Dict, source: str = "api", compute_id: str = None, ttl: int = None):
    now = datetime.utcnow()
    return {
        "data": data,
        "metadata": {
            "created_at": now.isoformat(),  # Current time
            "updated_at": now.isoformat(),  # Current time
            "source": source,
            "compute_id": compute_id,
            "ttl": ttl
        }
    }
```

#### `update_features_with_metadata()`
Used for **EXISTING** items:
```python
def update_features_with_metadata(data: Dict, existing_metadata: Dict = None, source: str = "api", compute_id: str = None, ttl: int = None):
    now = datetime.utcnow()
    
    if existing_metadata:
        # Preserve original created_at, update updated_at
        return {
            "data": data,
            "metadata": {
                "created_at": existing_metadata.get("created_at", now.isoformat()),  # PRESERVED
                "updated_at": now.isoformat(),  # CURRENT TIME
                "source": source,
                "compute_id": compute_id,
                "ttl": ttl
            }
        }
    else:
        # No existing metadata - treat as new item
        return create_features_with_metadata(data, source, compute_id, ttl)
```

### Logic Flow

1. **Check if item exists** in DynamoDB
2. **If item exists**:
   - Extract existing metadata
   - Preserve `created_at` from existing metadata
   - Set `updated_at` to current time
3. **If item doesn't exist**:
   - Set both `created_at` and `updated_at` to current time

## Test Scenarios

### Scenario 1: Create New Item
```bash
# Create initial item
curl -X POST "http://127.0.0.1:8000/items/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{"test_features": {"feature1": "initial_value", "feature2": 100}}'

# Result: Both created_at and updated_at are the same (current time)
```

### Scenario 2: Update Existing Item
```bash
# Wait a few seconds, then update
curl -X POST "http://127.0.0.1:8000/items/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{"test_features": {"feature1": "updated_value", "feature2": 200, "feature3": "new_feature"}}'

# Result: created_at preserved, updated_at changed to current time
```

### Scenario 3: Add New Category to Existing User
```bash
# Add new category to existing user
curl -X POST "http://127.0.0.1:8000/items/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{"new_category": {"featureA": "valueA", "featureB": 300}}'

# Result: New category gets fresh timestamps (both created_at and updated_at are current time)
```

### Scenario 4: Explicit Metadata
```bash
# Create with explicit metadata
curl -X POST "http://127.0.0.1:8000/items/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{"user_features": {
    "data": {"age": 25, "income": 50000}, 
    "metadata": {
      "created_at": "2025-10-06T08:00:00", 
      "updated_at": "2025-10-06T08:00:00", 
      "source": "ml_pipeline", 
      "compute_id": "batch_001", 
      "ttl": 3600
    }
  }}'

# Result: Explicit timestamps are preserved on updates
```

## Expected Behavior Summary

| Scenario | created_at | updated_at | Notes |
|----------|------------|------------|-------|
| **New Item** | Current time | Current time | Both timestamps are the same |
| **Update Existing** | **Preserved** | Current time | created_at stays constant |
| **New Category** | Current time | Current time | Fresh timestamps for new category |
| **Explicit Metadata** | **Preserved** | Current time | Respects explicit timestamps |

## Testing

Run the comprehensive test script:
```bash
./test_metadata_behavior.sh
```

This script tests all scenarios and validates:
- ✅ `created_at` is preserved during updates
- ✅ `updated_at` changes to current time during updates
- ✅ New items get fresh timestamps
- ✅ New categories get fresh timestamps
- ✅ Explicit metadata is handled correctly

## Benefits

1. **Audit Trail**: Track when data was originally created vs. last modified
2. **Data Integrity**: Prevent accidental overwriting of creation timestamps
3. **Compliance**: Meet regulatory requirements for data lineage
4. **Debugging**: Easily identify when data was first created vs. last updated
5. **Analytics**: Analyze data freshness and update patterns

## Error Handling

- If existing metadata is malformed, falls back to treating as new item
- If `created_at` is missing from existing metadata, uses current time
- Graceful degradation ensures system continues to function

## Monitoring

The metadata behavior is tracked through StatsD metrics:
- `feature_store.write.multi_category.success` - Successful writes
- `feature_store.dynamodb.put_item.success` - DynamoDB operations
- Timing metrics for performance monitoring

All metrics include relevant tags for filtering and analysis.
