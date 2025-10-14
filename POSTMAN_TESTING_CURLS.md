# Postman Testing - Curl Commands

## Base Configuration
- **Base URL**: `http://127.0.0.1:8015/api/v1`
- **Test Entity Value**: `postman_testing`
- **Test Entity Type**: `bright_uid`

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
  "tables_available": ["feature_store_bright_uid", "feature_store_account_uid"],
  "timestamp": "2025-10-14T12:34:56.789Z"
}
```

---

## 2. Write/Upsert Endpoint

### POST /items - Write Features

#### Test Case 1: Write to d0_unauth_features
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
      "feature_list": [
        {
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
      ]
    }
  }'
```

#### Test Case 2: Write to ncr_unauth_features
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
      "feature_list": [
        {
          "category": "ncr_unauth_features",
          "features": {
            "num_of_transactions": 25,
            "avg_transaction_amount": 125.50,
            "last_transaction_date": "2025-10-14",
            "merchant_category": "retail",
            "transaction_velocity": "medium"
          }
        }
      ]
    }
  }'
```

#### Test Case 3: Write to Multiple Categories
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
      "feature_list": [
        {
          "category": "d0_unauth_features",
          "features": {
            "credit_score": 800,
            "credit_utilization": 0.25
          }
        },
        {
          "category": "ncr_unauth_features",
          "features": {
            "num_of_transactions": 30,
            "total_spend": 5000
          }
        }
      ]
    }
  }'
```

#### Test Case 4: Invalid Category (Should Fail)
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
      "feature_list": [
        {
          "category": "invalid_category",
          "features": {
            "test_feature": 123
          }
        }
      ]
    }
  }'
```

**Expected Error:**
```json
{
  "detail": "Category 'invalid_category' is not allowed for write operations. Allowed categories: d0_unauth_features, ncr_unauth_features"
}
```

#### Test Case 5: Invalid Source (Should Fail)
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
      "feature_list": [
        {
          "category": "d0_unauth_features",
          "features": {
            "test_feature": 123
          }
        }
      ]
    }
  }'
```

**Expected Error:**
```json
{
  "detail": "Unauthorized source. Only 'prediction_service' is allowed to write features."
}
```

**Expected Success Response:**
```json
{
  "message": "Features upserted successfully",
  "entity_type": "bright_uid",
  "entity_value": "postman_testing",
  "categories_updated": ["d0_unauth_features"],
  "timestamp": "2025-10-14T12:34:56.789Z"
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
  },
  "meta": {
    "created_at": "2025-10-14T12:34:56.789Z",
    "updated_at": "2025-10-14T12:34:56.789Z",
    "compute_id": null
  }
}
```

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
  "features": {
    "d0_unauth_features": {
      "data": {
        "credit_score": 750,
        "debt_to_income_ratio": 0.35,
        "payment_history_score": 85.5
      },
      "meta": {
        "created_at": "2025-10-14T12:34:56.789Z",
        "updated_at": "2025-10-14T12:34:56.789Z",
        "compute_id": null
      }
    },
    "ncr_unauth_features": {
      "data": {
        "num_of_transactions": 25,
        "avg_transaction_amount": 125.50
      },
      "meta": {
        "created_at": "2025-10-14T12:34:56.789Z",
        "updated_at": "2025-10-14T12:34:56.789Z",
        "compute_id": null
      }
    }
  },
  "unavailable_feature_categories": []
}
```

---

## 5. Account UID Testing

### Write Features for account_uid
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "prediction_service"
    },
    "data": {
      "entity_type": "account_uid",
      "entity_value": "postman_testing",
      "feature_list": [
        {
          "category": "d0_unauth_features",
          "features": {
            "account_balance": 15000.50,
            "account_status": "active",
            "last_activity_date": "2025-10-14"
          }
        }
      ]
    }
  }'
```

### Read Single Category for account_uid
```bash
curl -X GET "http://127.0.0.1:8015/api/v1/get/item/postman_testing/d0_unauth_features?entity_type=account_uid"
```

### Read Multiple Features for account_uid
```bash
curl -X POST "http://127.0.0.1:8015/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "source": "api"
    },
    "data": {
      "entity_type": "account_uid",
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
      "entity_type": "bright_uid"
    }
  }'
```

**Expected Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "data", "entity_value"],
      "msg": "field required",
      "type": "value_error.missing"
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
      "feature_list": [
        {
          "category": "d0_unauth_features",
          "features": {
            "test_feature": 123
          }
        }
      ]
    }
  }'
```

### Empty Feature List
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
      "feature_list": []
    }
  }'
```

---

## 7. Testing Workflow

### Complete Test Sequence
```bash
# Step 1: Check health
curl -X GET "http://127.0.0.1:8015/api/v1/health"

# Step 2: Write features to d0_unauth_features
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"source": "prediction_service"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": [{
        "category": "d0_unauth_features",
        "features": {
          "credit_score": 750,
          "debt_to_income_ratio": 0.35,
          "payment_history_score": 85.5
        }
      }]
    }
  }'

# Step 3: Write features to ncr_unauth_features
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"source": "prediction_service"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": [{
        "category": "ncr_unauth_features",
        "features": {
          "num_of_transactions": 25,
          "avg_transaction_amount": 125.50
        }
      }]
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

# Step 7: Update existing features
curl -X POST "http://127.0.0.1:8015/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"source": "prediction_service"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "postman_testing",
      "feature_list": [{
        "category": "d0_unauth_features",
        "features": {
          "credit_score": 800,
          "new_feature": "updated_value"
        }
      }]
    }
  }'

# Step 8: Verify the update
curl -X GET "http://127.0.0.1:8015/api/v1/get/item/postman_testing/d0_unauth_features?entity_type=bright_uid"
```

---

## Notes

1. **Entity Value**: All tests use `postman_testing` as the entity_value for easy identification
2. **Allowed Categories**: Only `d0_unauth_features` and `ncr_unauth_features` are allowed for writes
3. **Source Validation**: Write operations only accept `source: "prediction_service"`
4. **Timestamps**: All responses include ISO 8601 timestamps with milliseconds and UTC timezone
5. **Wildcard**: Use `category:*` to retrieve all features from a category
6. **Meta vs Metadata**: The API uses `meta` (not `metadata`) in all request/response payloads

---

**Last Updated**: October 14, 2025
**API Version**: v1
**Server**: http://127.0.0.1:8015

