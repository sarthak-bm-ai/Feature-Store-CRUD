# Category Validation for Write Operations

## Overview
Implemented category validation to ensure only allowed categories can be written to the Feature Store. This prevents unauthorized or invalid categories from being created in the database.

## Implementation Details

### 1. Configuration (`core/settings.py`)

Added `ALLOWED_WRITE_CATEGORIES` configuration:

```python
class Settings:
    def __init__(self):
        # ... other configurations
        
        # Allowed Categories for Write Operations
        self.ALLOWED_WRITE_CATEGORIES = [
            "d0_unauth_features",
            "ncr_unauth_features"
        ]
```

**Environment Variable Support:**
You can optionally add environment variable support:
```python
self.ALLOWED_WRITE_CATEGORIES = os.getenv(
    "ALLOWED_WRITE_CATEGORIES", 
    "d0_unauth_features,ncr_unauth_features"
).split(",")
```

### 2. Service Layer Validation (`components/features/services.py`)

Added a new validation method:

```python
@staticmethod
def validate_category_for_write(category: str) -> None:
    """
    Validate that category is allowed for write operations.
    
    Args:
        category: Category name to validate
        
    Raises:
        ValueError: If category is not in allowed list
    """
    allowed_categories = settings.ALLOWED_WRITE_CATEGORIES
    
    if category not in allowed_categories:
        logger.error(f"Category '{category}' not in allowed write categories: {allowed_categories}")
        raise ValueError(
            f"Category '{category}' is not allowed for write operations. "
            f"Allowed categories: {', '.join(allowed_categories)}"
        )
    
    logger.debug(f"Category validated for write: {category}")
```

### 3. Integration in `validate_items()`

Updated the `validate_items()` method to call category validation:

```python
@staticmethod
def validate_items(items: Dict[str, Dict]) -> None:
    """Validate items for upsert operations."""
    # ... existing validation
    
    for category, features in items.items():
        # ... existing type checks
        
        # Validate category is in allowed list for write operations
        FeatureServices.validate_category_for_write(category)
        
        # ... rest of validation
```

## Allowed Categories

### Current Allowed Categories (as of implementation)
1. **`d0_unauth_features`** - D0 unauthenticated features
2. **`ncr_unauth_features`** - NCR unauthenticated features

### Adding New Categories

To add more allowed categories, update `core/settings.py`:

```python
self.ALLOWED_WRITE_CATEGORIES = [
    "d0_unauth_features",
    "ncr_unauth_features",
    "new_category_name",  # Add new category here
]
```

Or use environment variable:
```bash
export ALLOWED_WRITE_CATEGORIES="d0_unauth_features,ncr_unauth_features,new_category"
```

## API Behavior

### Write Operations (POST `/api/v1/items`)

**✅ Allowed Category - Success:**
```bash
curl -X POST "http://localhost:8000/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"source": "prediction_service"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "user-123",
      "feature_list": [{
        "category": "d0_unauth_features",
        "features": {
          "feature1": 100
        }
      }]
    }
  }'
```

**Response (200 OK):**
```json
{
  "message": "Items written successfully (full replace per category)",
  "entity_value": "user-123",
  "entity_type": "bright_uid",
  "results": {
    "d0_unauth_features": {
      "status": "replaced",
      "feature_count": 1
    }
  },
  "total_features": 1
}
```

**❌ Disallowed Category - Error:**
```bash
curl -X POST "http://localhost:8000/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"source": "prediction_service"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "user-123",
      "feature_list": [{
        "category": "unauthorized_category",
        "features": {
          "feature1": 100
        }
      }]
    }
  }'
```

**Response (400 Bad Request):**
```json
{
  "detail": "Category 'unauthorized_category' is not allowed for write operations. Allowed categories: d0_unauth_features, ncr_unauth_features"
}
```

### Read Operations (No Restriction)

**Important:** Category validation only applies to **write operations** (POST `/api/v1/items`).

Read operations are **NOT restricted**:
- `GET /api/v1/get/item/{entity_value}/{category}` ✅ Can read any category
- `POST /api/v1/get/items` ✅ Can read any category

This allows:
- Reading historical data from other categories
- Flexibility for read-only operations
- Migration and data analysis

## Validation Flow

```
POST /api/v1/items Request
    ↓
Routes (api/v1/routes.py)
    ↓
Controller (components/features/controller.py)
    ↓
Services.validate_items() (components/features/services.py)
    ↓
Services.validate_category_for_write() ← CATEGORY VALIDATION
    ↓
✅ Category in allowed list → Continue
❌ Category not in allowed list → Raise ValueError (400 Bad Request)
    ↓
Flows.upsert_features_flow()
    ↓
CRUD.upsert_item_with_meta()
    ↓
DynamoDB
```

## Security Benefits

1. **Prevents Unauthorized Writes**: Only whitelisted categories can be written
2. **Schema Enforcement**: Ensures data consistency across the system
3. **Audit Trail**: Logs all rejected category attempts
4. **Configuration-Driven**: Easy to update allowed categories without code changes
5. **Clear Error Messages**: Users know exactly which categories are allowed

## Logging

Category validation generates the following logs:

**Success:**
```
DEBUG - Category validated for write: d0_unauth_features
```

**Failure:**
```
ERROR - Category 'unauthorized_category' not in allowed write categories: ['d0_unauth_features', 'ncr_unauth_features']
```

## Metrics

Category validation failures are tracked via metrics:

```python
metrics.increment_counter(
    "write.multi_category.error",
    tags={
        "error_type": "invalid_category",
        "entity_type": entity_type
    }
)
```

## Testing

### Manual Test Script

Use the provided test script:
```bash
./test_category_validation.sh
```

### Unit Test Example

```python
def test_category_validation():
    # Test allowed category
    FeatureServices.validate_category_for_write("d0_unauth_features")  # Should pass
    
    # Test disallowed category
    with pytest.raises(ValueError) as exc_info:
        FeatureServices.validate_category_for_write("invalid_category")
    
    assert "not allowed for write operations" in str(exc_info.value)
    assert "d0_unauth_features" in str(exc_info.value)
```

## Migration Guide

### Before (No Validation)
Any category could be written:
```python
# This would succeed
POST /api/v1/items
{
  "category": "any_random_category",
  "features": {...}
}
```

### After (With Validation)
Only allowed categories can be written:
```python
# This succeeds
POST /api/v1/items
{
  "category": "d0_unauth_features",  # ✅ Allowed
  "features": {...}
}

# This fails
POST /api/v1/items
{
  "category": "random_category",  # ❌ Not allowed
  "features": {...}
}
```

## Configuration Management

### Development Environment
```python
# settings.py
ALLOWED_WRITE_CATEGORIES = [
    "d0_unauth_features",
    "ncr_unauth_features",
    "test_category"  # Additional test category for dev
]
```

### Production Environment
```python
# settings.py
ALLOWED_WRITE_CATEGORIES = [
    "d0_unauth_features",
    "ncr_unauth_features"
]
```

### Using Environment Variables
```bash
# .env file
ALLOWED_WRITE_CATEGORIES=d0_unauth_features,ncr_unauth_features

# In settings.py
self.ALLOWED_WRITE_CATEGORIES = os.getenv(
    "ALLOWED_WRITE_CATEGORIES",
    "d0_unauth_features,ncr_unauth_features"
).split(",")
```

## Future Enhancements

1. **Role-Based Category Access**: Different roles can write to different categories
2. **Dynamic Category Management**: Admin API to add/remove allowed categories
3. **Category-Specific Validation Rules**: Different validation rules per category
4. **Category Metadata**: Store metadata about each category (description, owner, etc.)
5. **Category Deprecation**: Mark categories as deprecated with warnings

## Related Files

- `core/settings.py` - Configuration
- `components/features/services.py` - Validation logic
- `components/features/controller.py` - Controller integration
- `api/v1/routes.py` - Error handling fix (removed invalid `response_model` from HTTPException)

## Bug Fix: HTTPException Error Handling

### Issue
The initial implementation had `response_model` parameter in `HTTPException`, which is not a valid parameter:
```python
raise HTTPException(status_code=400, detail=str(e), response_model=ErrorResponseSchema)  # ❌ Invalid
```

### Fix
Removed the invalid parameter:
```python
raise HTTPException(status_code=400, detail=str(e))  # ✅ Correct
```

FastAPI automatically formats error responses according to its standard error schema.

---

**Implementation Status:** ✅ Complete & Tested
**Date:** October 14, 2025
**Version:** 1.0.0


