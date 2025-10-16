# Postman Testing - Curl Commands

## Base Configuration
- **Base URL**: `http://127.0.0.1:8015/api/v1`
- **Test Entity Value**: `postman_testing`
- **Test Entity Type**: `bright_uid` or `account_pid`

---

## 1. Health Check Endpoint

### GET /health
```bash
curl -X GET "http://127.0.0.1:8015/api/v1/health"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "dynamodb_connection": true,
  "tables_available": [],
  "timestamp": "2025-10-16T12:34:56.789Z"
}
```

**Note**: Health check is now service-level only and does not perform DynamoDB connection checks.

---

## 2. Write/Upsert Endpoint (Single Category)

### POST /items - Write Single Category Features

**Important**: The API now accepts **single category writes only**. Each request writes to one category at a time.

#### Test Case 1: Write to d0_unauth_features (with compute_id)
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service",
      "compute_id": "spark-job-2025-10-16-abc123"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "category": "d0_unauth_features",
      "features": {
        "credit_score": 750,
        "debt_to_income_ratio": 0.35,
        "payment_history_score": 85.5,
        "account_age_months": 36,
        "total_credit_limit": 50000,
        "is_verified": true,
        "risk_level": "low"
      }
    }
  }'
```

**Expected Success Response:**
```json
{
  "message": "Category written successfully (full replace)",
  "entity_value": "postman_testing",
  "entity_type": "bright_uid",
  "category": "d0_unauth_features",
  "feature_count": 7
}
```

#### Test Case 2: Write to ncr_unauth_features (without compute_id)
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "category": "ncr_unauth_features",
      "features": {
        "num_of_transactions": 25,
        "avg_transaction_amount": 125.50,
        "last_transaction_date": "2025-10-14",
        "merchant_category": "retail",
        "transaction_velocity": "medium"
      }
    }
  }'
```

**Expected Success Response:**
```json
{
  "message": "Category written successfully (full replace)",
  "entity_value": "postman_testing",
  "entity_type": "bright_uid",
  "category": "ncr_unauth_features",
  "feature_count": 5
}
```

**Note**: When `compute_id` is not provided, it will be stored as `null` in the metadata.

#### Test Case 3: Write with Different Compute Job ID
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service",
      "compute_id": "airflow-dag-2025-10-16-xyz789"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "category": "d0_unauth_features",
      "features": {
        "credit_score": 800,
        "credit_utilization": 0.25
      }
    }
  }'
```

**Expected Success Response:**
```json
{
  "message": "Category written successfully (full replace)",
  "entity_value": "postman_testing",
  "entity_type": "bright_uid",
  "category": "d0_unauth_features",
  "feature_count": 2
}
```

**Note**: To write multiple categories, make separate API calls for each category.

#### Test Case 4: Invalid Category (Should Fail - 400)
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service",
      "compute_id": null
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "category": "invalid_category",
      "features": {
        "test_feature": 123
      }
    }
  }'
```

**Expected Error (HTTP 400):**
```json
{
  "detail": "Category 'invalid_category' is not allowed for write operations. Allowed categories: d0_unauth_features, ncr_unauth_features"
}
```

#### Test Case 5: Invalid Source (Should Fail - 422)
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "unauthorized_source"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "category": "d0_unauth_features",
      "features": {
        "test_feature": 123
      }
    }
  }'
```

**Expected Error (HTTP 422 - Pydantic Validation):**
```json
{
  "detail": [
    {
      "loc": ["body", "meta", "source"],
      "msg": "Only prediction_service is allowed for write operations",
      "type": "value_error"
    }
  ]
}
```

---

## 3. Read Single Category Endpoint

### GET /get/item/{entity_value}/{category}

#### Test Case 1: Read d0_unauth_features
```bash
curl -X GET "http://127.0.0.1:8015/api/v1/get/item/postman_testing/d0_unauth_features?entity_type=bright_uid"
```

#### Test Case 2: Read ncr_unauth_features
```bash
curl -X GET "http://127.0.0.1:8015/api/v1/get/item/postman_testing/ncr_unauth_features?entity_type=bright_uid"
```

#### Test Case 3: Read Non-existent Category (Should Return Empty)
```bash
curl -X GET "http://127.0.0.1:8015/api/v1/get/item/postman_testing/non_existent_category?entity_type=bright_uid"
```

**Expected Success Response:**
```json
{
  "bright_uid": "postman_testing",
  "category": "d0_unauth_features",
  "features": {
    "data": {
      "credit_score": 750,
      "debt_to_income_ratio": 0.35,
      "payment_history_score": 85.5,
      "account_age_months": 36,
      "total_credit_limit": 50000,
      "is_verified": true,
      "risk_level": "low"
    },
    "meta": {
      "created_at": "2025-10-16T12:34:56.789Z",
      "updated_at": "2025-10-16T12:34:56.789Z",
      "compute_id": "spark-job-2025-10-16-abc123"
    }
  }
}
```

**Note**: The `compute_id` in the response reflects what was provided in the write request.

---

## 4. Read Multiple Features Endpoint

### POST /get/items - Read Specific Features

#### Test Case 1: Read Specific Features from Single Category
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "api"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": [
        "d0_unauth_features:credit_score",
        "d0_unauth_features:debt_to_income_ratio",
        "d0_unauth_features:payment_history_score"
      ]
    }
  }'
```

#### Test Case 2: Read All Features from Category (Wildcard)
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "api"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": [
        "d0_unauth_features:*"
      ]
    }
  }'
```

#### Test Case 3: Read Features from Multiple Categories
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "api"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": [
        "d0_unauth_features:credit_score",
        "d0_unauth_features:debt_to_income_ratio",
        "ncr_unauth_features:num_of_transactions",
        "ncr_unauth_features:avg_transaction_amount"
      ]
    }
  }'
```

#### Test Case 4: Mix Wildcard and Specific Features
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "api"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": [
        "d0_unauth_features:*",
        "ncr_unauth_features:num_of_transactions"
      ]
    }
  }'
```

#### Test Case 5: Request Non-existent Features
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "api"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": [
        "d0_unauth_features:non_existent_feature",
        "d0_unauth_features:another_missing_feature"
      ]
    }
  }'
```

**Expected Success Response:**
```json
{
  "entity_type": "bright_uid",
  "entity_value": "postman_testing",
  "items": {
    "d0_unauth_features": {
      "bright_uid": "postman_testing",
      "category": "d0_unauth_features",
      "features": {
        "data": {
          "credit_score": 750,
          "debt_to_income_ratio": 0.35,
          "payment_history_score": 85.5
        },
        "meta": {
          "created_at": "2025-10-16T12:34:56.789Z",
          "updated_at": "2025-10-16T12:34:56.789Z",
          "compute_id": "spark-job-2025-10-16-abc123"
        }
      }
    },
    "ncr_unauth_features": {
      "bright_uid": "postman_testing",
      "category": "ncr_unauth_features",
      "features": {
        "data": {
          "num_of_transactions": 25,
          "avg_transaction_amount": 125.50
        },
        "meta": {
          "created_at": "2025-10-16T12:34:56.789Z",
          "updated_at": "2025-10-16T12:34:56.789Z",
          "compute_id": "airflow-dag-2025-10-16-xyz789"
        }
      }
    }
  },
  "unavailable_feature_categories": []
}
```

**Note**: Each category can have a different `compute_id` based on which compute job wrote it.

---

## 5. Account PID Testing

### Write Features for account_pid
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service",
      "compute_id": "account-processor-2025-10-16-def456"
    },
    "data": {
      "entity_type": "account_pid",
      "entity_value": "postman_testing",
      "category": "d0_unauth_features",
      "features": {
        "account_balance": 15000.50,
        "account_status": "active",
        "last_activity_date": "2025-10-16"
      }
    }
  }'
```

**Expected Success Response:**
```json
{
  "message": "Category written successfully (full replace)",
  "entity_value": "postman_testing",
  "entity_type": "account_pid",
  "category": "d0_unauth_features",
  "feature_count": 3
}
```

### Read Single Category for account_pid
```bash
curl -X GET "http://127.0.0.1:8015/api/v1/get/item/postman_testing/d0_unauth_features?entity_type=account_pid"
```

### Read Multiple Features for account_pid
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "api"
    },
    "data": {
      "entity_type": "account_pid",
      "entity_value": "postman_testing",
      "feature_list": [
        "d0_unauth_features:account_balance",
        "d0_unauth_features:account_status"
      ]
    }
  }'
```

---

## 6. Edge Cases & Error Scenarios

### Missing Required Fields
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing"
    }
  }'
```

**Expected Error (HTTP 422):**
```json
{
  "detail": [
    {
      "loc": ["body", "data"],
      "msg": "Missing required field: category",
      "type": "value_error"
    }
  ]
}
```

### Invalid Entity Type
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service"
    },
    "data": {
      "entity_type": "invalid_type",
      "entity_value": "postman_testing",
      "category": "d0_unauth_features",
      "features": {
        "test_feature": 123
      }
    }
  }'
```

**Expected Error (HTTP 422):**
```json
{
  "detail": [
    {
      "loc": ["body", "data"],
      "msg": "entity_type must be either \"bright_uid\" or \"account_pid\"",
      "type": "value_error"
    }
  ]
}
```

### Empty Features Dictionary
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "category": "d0_unauth_features",
      "features": {}
    }
  }'
```

**Expected Error (HTTP 422):**
```json
{
  "detail": [
    {
      "loc": ["body", "data"],
      "msg": "features must be a non-empty dictionary",
      "type": "value_error"
    }
  ]
}
```

---

## 7. Testing Workflow

### Complete Test Sequence
```bash
# Step 1: Check health
curl -X GET "http://127.0.0.1:8015/api/v1/health"

# Step 2: Write features to d0_unauth_features (with compute_id)
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service",
      "compute_id": "spark-job-2025-10-16-run1"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "category": "d0_unauth_features",
      "features": {
        "credit_score": 750,
        "debt_to_income_ratio": 0.35,
        "payment_history_score": 85.5
      }
    }
  }'

# Step 3: Write features to ncr_unauth_features (separate request, different compute_id)
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service",
      "compute_id": "airflow-dag-2025-10-16-task2"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "category": "ncr_unauth_features",
      "features": {
        "num_of_transactions": 25,
        "avg_transaction_amount": 125.50
      }
    }
  }'

# Step 4: Read single category
curl -X GET "http://127.0.0.1:8015/api/v1/get/item/postman_testing/d0_unauth_features?entity_type=bright_uid"

# Step 5: Read specific features from multiple categories
curl -X POST "http://127.0.0.1:8015/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"source": "api"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": [
        "d0_unauth_features:credit_score",
        "ncr_unauth_features:num_of_transactions"
      ]
    }
  }'

# Step 6: Read all features using wildcard
curl -X POST "http://127.0.0.1:8015/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"source": "api"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": ["d0_unauth_features:*", "ncr_unauth_features:*"]
    }
  }'

# Step 7: Update existing category (full replace with new compute_id)
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service",
      "compute_id": "spark-job-2025-10-16-run2"
    },
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "category": "d0_unauth_features",
      "features": {
        "credit_score": 800,
        "new_feature": "updated_value"
      }
    }
  }'

# Step 8: Verify the update (check compute_id changed)
curl -X GET "http://127.0.0.1:8015/api/v1/get/item/postman_testing/d0_unauth_features?entity_type=bright_uid"
```

---

## Notes

1. **Entity Value**: All tests use `postman_testing` as the entity_value for easy identification
2. **Entity Types**: `bright_uid` and `account_pid` (not `account_uid` - this was renamed)
3. **Allowed Categories**: Only `d0_unauth_features` and `ncr_unauth_features` are allowed for writes
4. **Source Validation**: Write operations only accept `source: "prediction_service"`
5. **Compute ID**: Optional field in write requests to track which compute job generated the features
   - If not provided, stored as `null`
   - Can be any string (e.g., "spark-job-id", "airflow-dag-id")
   - Returned in read responses within `features.meta.compute_id`
6. **Single Category Writes**: The `/items` endpoint now accepts only **one category per request**
   - To write multiple categories, make separate API calls
   - Each category can have its own `compute_id`
7. **Timestamps**: All responses include ISO 8601 timestamps with milliseconds and UTC timezone
8. **Wildcard**: Use `category:*` to retrieve all features from a category
9. **Meta vs Metadata**: The API uses `meta` (not `metadata`) in all request/response payloads
10. **Error Codes**:
    - `400`: Business logic validation errors (invalid category, etc.)
    - `404`: Resource not found
    - `422`: Pydantic validation errors (invalid schema, missing fields, etc.)
    - `500`: Internal server errors
11. **Health Check**: Simplified to service-level only, no longer checks DynamoDB connection

---

**Last Updated**: October 16, 2025
**API Version**: v1
**Server**: http://127.0.0.1:8015

## Recent Changes

### October 16, 2025
- **Compute ID Support**: Added `compute_id` field to write request metadata for tracking compute jobs
- **Single Category Writes**: Refactored `/items` endpoint to accept only single category per request
- **Entity Type Rename**: `account_uid` renamed to `account_pid` throughout the API
- **Health Check Simplification**: Removed DynamoDB connection checks from health endpoint
- **Error Handling**: Improved error categorization with specific HTTP status codes




