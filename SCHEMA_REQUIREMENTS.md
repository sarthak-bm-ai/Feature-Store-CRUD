# Simplified API Documentation

## Overview
The Feature Store API now uses a **simplified approach** where users provide simple feature data, and the system automatically handles metadata generation and management.

## User-Friendly Schema Format

Users only need to provide simple feature data:

```json
{
  "category_name": {
    "feature1": "value1",
    "feature2": 123.45,
    "feature3": true
  }
}
```

The system automatically wraps this in the internal schema with metadata:

```json
{
  "category_name": {
    "data": {
      "feature1": "value1",
      "feature2": 123.45,
      "feature3": true
    },
    "metadata": {
      "created_at": "2025-10-06T09:11:06.099812",  // Auto-generated
      "updated_at": "2025-10-06T09:11:06.099812",  // Auto-generated
      "source": "api",                              // Default
      "compute_id": "None",                         // Default
      "ttl": "None"                                 // Default
    }
  }
}
```

## How It Works

### User Input (Simple)
Users provide simple feature data without worrying about metadata:

```json
{
  "trans_features": {
    "avg_credit_30d": 150.5,
    "num_transactions": 25
  },
  "user_features": {
    "age": 25,
    "income": 50000
  }
}
```

### System Processing (Automatic)
The system automatically:

1. **Wraps features in `data` field**
2. **Generates metadata with timestamps**
3. **Handles create vs update logic**

### Metadata Behavior

#### New Category (First Time)
- **`created_at`**: Current timestamp
- **`updated_at`**: Current timestamp (same as created_at)
- **`source`**: "api" (default)
- **`compute_id`**: "None" (default)
- **`ttl`**: "None" (default)

#### Existing Category (Update)
- **`created_at`**: **PRESERVED** from original creation
- **`updated_at`**: **UPDATED** to current timestamp
- **`source`**: "api" (default)
- **`compute_id`**: "None" (default)
- **`ttl`**: "None" (default)

## API Examples

### ✅ Write New Features (Simple Format)
```bash
curl -X POST "http://127.0.0.1:8000/items/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{
    "trans_features": {
      "avg_credit_30d": 150.5,
      "num_transactions": 25
    },
    "user_features": {
      "age": 25,
      "income": 50000
    }
  }'
```

**Response**:
```json
{
  "message": "Items written successfully (full replace per category)",
  "identifier": "user123",
  "table_type": "bright_uid",
  "results": {
    "trans_features": {"status": "replaced", "feature_count": 2},
    "user_features": {"status": "replaced", "feature_count": 2}
  },
  "total_features": 4
}
```

### ✅ Update Existing Features
```bash
curl -X POST "http://127.0.0.1:8000/items/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{
    "trans_features": {
      "avg_credit_30d": 200.0,
      "num_transactions": 30,
      "new_feature": "value"
    }
  }'
```

**Result**: `created_at` is preserved, `updated_at` is updated to current time.

### ✅ Read Single Category
```bash
curl "http://127.0.0.1:8000/get/item/user123/trans_features?table_type=bright_uid"
```

**Response**:
```json
{
  "bright_uid": "user123",
  "category": "trans_features",
  "features": {
    "data": {
      "avg_credit_30d": 200.0,
      "num_transactions": 30,
      "new_feature": "value"
    },
    "metadata": {
      "created_at": "2025-10-06T09:11:06.099812",
      "updated_at": "2025-10-06T09:11:22.610553",
      "source": "api",
      "compute_id": "None",
      "ttl": "None"
    }
  }
}
```

### ✅ Read Multiple Categories with Filtering
```bash
curl -X POST "http://127.0.0.1:8000/get/item/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{
    "trans_features": ["avg_credit_30d"],
    "user_features": ["age"]
  }'
```

**Response**:
```json
{
  "identifier": "user123",
  "table_type": "bright_uid",
  "items": {
    "trans_features": {
      "bright_uid": "user123",
      "category": "trans_features",
      "features": {
        "data": {"avg_credit_30d": 200.0},
        "metadata": {
          "created_at": "2025-10-06T09:11:06.099812",
          "updated_at": "2025-10-06T09:11:22.610553",
          "source": "api",
          "compute_id": "None",
          "ttl": "None"
        }
      }
    },
    "user_features": {
      "bright_uid": "user123",
      "category": "user_features",
      "features": {
        "data": {"age": 25},
        "metadata": {
          "created_at": "2025-10-06T09:11:36.641218",
          "updated_at": "2025-10-06T09:11:36.641218",
          "source": "api",
          "compute_id": "None",
          "ttl": "None"
        }
      }
    }
  },
  "missing_categories": []
}
```

## Read Operations

Read operations return data in the new schema format:

### Single Category Read
```bash
curl "http://127.0.0.1:8000/get/item/user123/trans_features?table_type=bright_uid"
```

**Response**:
```json
{
  "bright_uid": "user123",
  "category": "trans_features",
  "features": {
    "data": {
      "avg_credit_30d": 150.5,
      "num_transactions": 25
    },
    "metadata": {
      "created_at": "2025-10-06T08:00:00",
      "updated_at": "2025-10-06T08:59:27.837898",
      "source": "ml_pipeline",
      "compute_id": "batch_001",
      "ttl": 3600
    }
  }
}
```

### Filtered Multi-Category Read
```bash
curl -X POST "http://127.0.0.1:8000/get/item/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{
    "trans_features": ["avg_credit_30d"],
    "balance_features": ["avg_30d_bal"]
  }'
```

**Response**:
```json
{
  "identifier": "user123",
  "table_type": "bright_uid",
  "items": {
    "trans_features": {
      "bright_uid": "user123",
      "category": "trans_features",
      "features": {
        "data": {
          "avg_credit_30d": 150.5
        },
        "metadata": {
          "created_at": "2025-10-06T08:00:00",
          "updated_at": "2025-10-06T08:59:27.837898",
          "source": "ml_pipeline",
          "compute_id": "batch_001",
          "ttl": 3600
        }
      }
    },
    "balance_features": {
      "bright_uid": "user123",
      "category": "balance_features",
      "features": {
        "data": {
          "avg_30d_bal": 3000.0
        },
        "metadata": {
          "created_at": "2025-10-06T08:00:00",
          "updated_at": "2025-10-06T08:00:00",
          "source": "api",
          "compute_id": null,
          "ttl": null
        }
      }
    }
  },
  "missing_categories": []
}
```

## Migration from Old Format

If you have existing data in the old format (without `data` and `metadata` structure), you will need to:

1. **Read existing data** using the read endpoints
2. **Transform the data** to the new schema format
3. **Write back** using the write endpoint with the new format

### Migration Example

**Step 1**: Read existing data
```bash
curl "http://127.0.0.1:8000/get/item/user123/trans_features?table_type=bright_uid"
```

**Step 2**: Transform to new format (in your application code)
```python
# Old format
old_data = {
    "bright_uid": "user123",
    "category": "trans_features",
    "features": {
        "avg_credit_30d": 150.5,
        "num_transactions": 25
    }
}

# Transform to new format
new_data = {
    "trans_features": {
        "data": old_data["features"],
        "metadata": {
            "source": "migration",
            "compute_id": "migration_job_001",
            "ttl": 86400
        }
    }
}
```

**Step 3**: Write back in new format
```bash
curl -X POST "http://127.0.0.1:8000/items/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{
    "trans_features": {
      "data": {
        "avg_credit_30d": 150.5,
        "num_transactions": 25
      },
      "metadata": {
        "source": "migration",
        "compute_id": "migration_job_001",
        "ttl": 86400
      }
    }
  }'
```

## Benefits of New Schema

1. **Audit Trail**: Track when data was created and last updated
2. **Data Lineage**: Know the source and computation that generated the data
3. **TTL Support**: Automatic expiration of stale data
4. **Consistency**: Uniform structure across all feature categories
5. **Extensibility**: Easy to add new metadata fields in the future

## Error Messages

| Error | HTTP Code | Description |
|-------|-----------|-------------|
| Missing `data` field | 400 | The request body must include a `data` field |
| Missing `metadata` field | 400 | The request body must include a `metadata` field |
| Invalid table_type | 400 | table_type must be 'bright_uid' or 'account_id' |
| Item not found | 404 | The requested item does not exist |
| Empty request body | 400 | The request body cannot be empty |

## Best Practices

1. **Always provide source**: Helps with debugging and data lineage
2. **Use compute_id for batch jobs**: Makes it easy to track which job generated the data
3. **Set appropriate TTL**: Prevents stale data from accumulating
4. **Use descriptive feature names**: Makes the data self-documenting
5. **Validate data before writing**: Ensure data quality at the source

## Summary

- ✅ **Required**: Both `data` and `metadata` fields
- ✅ **Auto-generated**: `created_at` and `updated_at` if not provided
- ✅ **Preserved**: `created_at` on updates
- ✅ **Updated**: `updated_at` on every write
- ❌ **Not Supported**: Old format without `data` and `metadata`
