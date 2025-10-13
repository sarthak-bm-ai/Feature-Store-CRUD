# Timestamp Consistency Implementation

## Overview

Implemented centralized timestamp handling to ensure consistency across the entire Feature Store service. All timestamps are now in **ISO 8601 format with milliseconds precision** and timezone information.

## Timestamp Format Standard

### Format Specification
```
ISO 8601 with milliseconds and timezone
Format: YYYY-MM-DDTHH:MM:SS.ffffff+00:00
Example: 2025-10-13T08:12:47.751080+00:00
```

### Why This Format?

1. **ISO 8601 Standard**: Internationally recognized datetime format
2. **Milliseconds Precision**: Captures precise timing for audit trails
3. **Timezone Aware**: Always UTC (+00:00) to avoid timezone confusion
4. **Sortable**: Lexicographic sorting works correctly
5. **Human Readable**: Easy to read and debug
6. **Machine Parseable**: Standard libraries can parse it easily

## Implementation

### 1. Centralized Timestamp Utility

**File**: `core/timestamp_utils.py`

#### Core Functions:

```python
def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format with milliseconds."""
    return datetime.now(timezone.utc).isoformat()
    # Returns: "2025-10-13T08:12:47.751080+00:00"
```

```python
def format_timestamp(dt: datetime) -> str:
    """Format a datetime object to ISO 8601 string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
```

```python
def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse an ISO 8601 timestamp string to datetime object."""
    # Handles multiple formats for backward compatibility
```

```python
def ensure_timestamp_consistency(timestamp: any) -> str:
    """Ensure timestamp is in consistent ISO 8601 format."""
    # Handles datetime, string, or None inputs
    # Always returns consistent ISO 8601 string
```

#### Helper Functions:

```python
def validate_timestamp_format(timestamp_str: str) -> bool:
    """Validate if a string is in correct ISO 8601 format."""
```

```python
def get_timestamp_metadata() -> dict:
    """Get standard timestamp metadata for new records."""
    # Returns: {"created_at": "...", "updated_at": "..."}
```

```python
def get_update_timestamp() -> dict:
    """Get timestamp metadata for updates (only updated_at)."""
    # Returns: {"updated_at": "..."}
```

### 2. Updated Components

#### A. CRUD Operations (`components/features/crud.py`)

**Before:**
```python
now = datetime.utcnow().isoformat()  # Deprecated, no timezone
```

**After:**
```python
from core.timestamp_utils import get_current_timestamp, ensure_timestamp_consistency

now = get_current_timestamp()  # ISO 8601 with timezone
```

**Timestamp Preservation:**
```python
# Preserve created_at on updates
if existing_item and "features" in existing_item:
    existing_features = dynamodb_to_dict(existing_item["features"])
    existing_created_at = existing_features.get("metadata", {}).get("created_at")
    # Ensure consistency even for old timestamps
    created_at = ensure_timestamp_consistency(existing_created_at) if existing_created_at else now
else:
    created_at = now
```

#### B. Kafka Publisher (`core/kafka_publisher.py`)

**Before:**
```python
"timestamp": datetime.now(timezone.utc).isoformat()
```

**After:**
```python
from core.timestamp_utils import get_current_timestamp

"timestamp": get_current_timestamp()
```

#### C. API Routes (`api/v1/routes.py`)

**Before:**
```python
from datetime import datetime
timestamp=datetime.utcnow().isoformat()  # Deprecated
```

**After:**
```python
from core.timestamp_utils import get_current_timestamp

timestamp=get_current_timestamp()
```

#### D. Pydantic Models (`components/features/models.py`)

Added validation to ensure timestamps are properly parsed:

```python
class FeatureMetadata(BaseModel):
    """Metadata for feature records with ISO 8601 timestamps."""
    created_at: datetime = Field(..., description="Creation timestamp in ISO 8601 format")
    updated_at: datetime = Field(..., description="Last update timestamp in ISO 8601 format")
    compute_id: Optional[str] = Field(None, description="Compute job ID")
    
    @validator('created_at', 'updated_at', pre=True)
    def parse_timestamp(cls, v):
        """Ensure timestamps are properly parsed from ISO 8601 strings."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # Try alternate formats for backward compatibility
                # ... fallback parsing logic
        return v
```

### 3. Type Conversion for DynamoDB

The `_convert_floats_to_decimal()` function in `crud.py` handles datetime conversion:

```python
def _convert_floats_to_decimal(obj):
    """Convert float to Decimal and datetime to string for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, datetime):
        return obj.isoformat()  # Converts to ISO 8601 string
    elif isinstance(obj, dict):
        return {k: _convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_floats_to_decimal(item) for item in obj]
    return obj
```

## Usage Examples

### Creating New Records

```python
from core.timestamp_utils import get_current_timestamp

# Get current timestamp
now = get_current_timestamp()
# Returns: "2025-10-13T08:12:47.751080+00:00"

# Create metadata
metadata = FeatureMetadata(
    created_at=now,
    updated_at=now,
    compute_id="compute-123"
)
```

### Updating Records

```python
from core.timestamp_utils import get_current_timestamp, ensure_timestamp_consistency

# Preserve existing created_at
existing_created_at = existing_record.get("created_at")
created_at = ensure_timestamp_consistency(existing_created_at)

# New updated_at
updated_at = get_current_timestamp()

metadata = FeatureMetadata(
    created_at=created_at,
    updated_at=updated_at,
    compute_id="compute-456"
)
```

### Parsing Timestamps

```python
from core.timestamp_utils import parse_timestamp

# Parse ISO 8601 string
timestamp_str = "2025-10-13T08:12:47.751080+00:00"
dt = parse_timestamp(timestamp_str)
# Returns: datetime object (timezone-aware)
```

### Validating Timestamps

```python
from core.timestamp_utils import validate_timestamp_format

is_valid = validate_timestamp_format("2025-10-13T08:12:47.751080+00:00")
# Returns: True

is_valid = validate_timestamp_format("invalid-timestamp")
# Returns: False
```

## Benefits

### 1. Consistency
- ✅ All timestamps use the same format across the service
- ✅ No mixing of timezone-aware and naive datetimes
- ✅ Consistent precision (milliseconds)

### 2. Reliability
- ✅ Centralized logic reduces bugs
- ✅ Validation ensures data integrity
- ✅ Backward compatibility with old formats

### 3. Maintainability
- ✅ Single source of truth for timestamp handling
- ✅ Easy to update format if needed
- ✅ Clear documentation and examples

### 4. Debugging
- ✅ Human-readable format
- ✅ Timezone information prevents confusion
- ✅ Millisecond precision for precise timing

### 5. Compliance
- ✅ ISO 8601 standard compliance
- ✅ Audit trail with precise timestamps
- ✅ Consistent data for analytics

## DynamoDB Storage

### Structure in DynamoDB

```json
{
  "features": {
    "data": {
      "M": {
        "feature1": {"N": "123"},
        "feature2": {"S": "value"}
      }
    },
    "metadata": {
      "M": {
        "created_at": {
          "S": "2025-10-13T08:12:47.751080+00:00"
        },
        "updated_at": {
          "S": "2025-10-13T08:15:30.123456+00:00"
        },
        "compute_id": {
          "S": "compute-123"
        }
      }
    }
  }
}
```

### Timestamp Fields

| Field | Type | Format | Description |
|-------|------|--------|-------------|
| `created_at` | String (S) | ISO 8601 | When the record was first created |
| `updated_at` | String (S) | ISO 8601 | When the record was last updated |

## Kafka Events

### Event Payload

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "feature_available",
  "timestamp": "2025-10-13T08:12:47.751080+00:00",
  "entity_type": "bright_uid",
  "entity_id": "user-123",
  "resource_type": "feature",
  "resource_name": "user_features",
  "compute_id": "compute-123",
  "features": ["age", "income", "city"]
}
```

All Kafka events include a `timestamp` field in ISO 8601 format.

## API Responses

### Health Check Response

```json
{
  "status": "healthy",
  "dynamodb_connection": true,
  "tables_available": ["bright_uid", "account_id"],
  "timestamp": "2025-10-13T08:12:47.751080+00:00"
}
```

### Feature Read Response

```json
{
  "entity_value": "user-123",
  "entity_type": "bright_uid",
  "items": {
    "user_features": {
      "features": {
        "data": {
          "age": 30,
          "income": 60000
        },
        "metadata": {
          "created_at": "2025-10-13T08:12:47.751080+00:00",
          "updated_at": "2025-10-13T08:15:30.123456+00:00",
          "compute_id": "compute-123"
        }
      }
    }
  }
}
```

## Migration Notes

### Backward Compatibility

The implementation handles old timestamp formats gracefully:

1. **Old Format** (naive datetime): `"2025-10-13 08:12:47.751080"`
2. **New Format** (ISO 8601 with timezone): `"2025-10-13T08:12:47.751080+00:00"`

The `ensure_timestamp_consistency()` function converts old formats to the new standard automatically.

### Existing Data

Existing records with old timestamp formats will be:
1. **Read correctly**: Parser handles multiple formats
2. **Converted on update**: Next update will use new format
3. **Validated**: Pydantic validators ensure consistency

No migration script needed - gradual conversion on updates.

## Testing

### Test Timestamp Generation

```python
from core.timestamp_utils import get_current_timestamp
import time

# Test timestamp generation
ts1 = get_current_timestamp()
time.sleep(0.001)  # Wait 1ms
ts2 = get_current_timestamp()

assert ts1 != ts2  # Millisecond precision
assert ts1 < ts2   # Sortable
```

### Test Timestamp Parsing

```python
from core.timestamp_utils import parse_timestamp, format_timestamp

# Test parsing
ts_str = "2025-10-13T08:12:47.751080+00:00"
dt = parse_timestamp(ts_str)
assert dt is not None

# Test round-trip
formatted = format_timestamp(dt)
assert formatted == ts_str
```

### Test Validation

```python
from core.timestamp_utils import validate_timestamp_format

# Valid formats
assert validate_timestamp_format("2025-10-13T08:12:47.751080+00:00") == True
assert validate_timestamp_format("2025-10-13T08:12:47+00:00") == True

# Invalid formats
assert validate_timestamp_format("invalid") == False
assert validate_timestamp_format("2025-13-45") == False
```

## Best Practices

### DO:
✅ Use `get_current_timestamp()` for new timestamps  
✅ Use `ensure_timestamp_consistency()` when handling existing timestamps  
✅ Always store timestamps as strings in DynamoDB  
✅ Use timezone-aware datetime objects in Python  
✅ Validate timestamps with Pydantic models  

### DON'T:
❌ Use `datetime.utcnow()` (deprecated, no timezone)  
❌ Use `datetime.now()` without timezone  
❌ Mix timestamp formats  
❌ Store datetime objects directly in DynamoDB  
❌ Assume timestamps are in local timezone  

## Troubleshooting

### Issue: Timestamp parsing fails

**Solution**: Check if the timestamp string is in ISO 8601 format. Use `ensure_timestamp_consistency()` to handle various formats.

### Issue: Timezone confusion

**Solution**: All timestamps are in UTC. Use `datetime.now(timezone.utc)` or `get_current_timestamp()`.

### Issue: Old timestamps not updating

**Solution**: Old timestamps are preserved on updates. Only `updated_at` changes. This is intentional for audit trails.

### Issue: DynamoDB type error with datetime

**Solution**: Use `_convert_floats_to_decimal()` which converts datetime to ISO 8601 string before storing.

## Conclusion

The timestamp consistency implementation ensures:

✅ **Standardization**: All timestamps in ISO 8601 format  
✅ **Precision**: Millisecond-level accuracy  
✅ **Reliability**: Centralized, tested utilities  
✅ **Maintainability**: Single source of truth  
✅ **Compatibility**: Handles old and new formats  

This provides a solid foundation for audit trails, analytics, and debugging across the entire Feature Store service.

