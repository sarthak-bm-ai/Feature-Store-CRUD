# Feature Store API Documentation

## Overview
This Feature Store API provides CRUD operations for managing feature data across two DynamoDB tables with different partition keys:
- **`features_bright_uid`**: Partition key = `bright_uid`
- **`features_account_id`**: Partition key = `account_id`

## Table of Contents
1. [API Endpoints](#api-endpoints)
2. [Metrics System](#metrics-system)
3. [Request/Response Examples](#requestresponse-examples)
4. [Error Handling](#error-handling)
5. [Schema Documentation](#schema-documentation)
6. [Monitoring Setup](#monitoring-setup)

---

## API Endpoints

### 1. Get Single Category Features
**Endpoint**: `GET /get/item/{identifier}/{category}`

**Parameters**:
- `identifier` (path): User/account identifier
- `category` (path): Feature category (e.g., `trans_features`, `balance_features`)
- `table_type` (query, optional): `bright_uid` or `account_id` (default: `bright_uid`)

**Response**: Full feature data for the category

### 2. Get Filtered Multi-Category Features
**Endpoint**: `POST /get/item/{identifier}`

**Parameters**:
- `identifier` (path): User/account identifier
- `table_type` (query, optional): `bright_uid` or `account_id` (default: `bright_uid`)

**Request Body**:
```json
{
  "category1": ["feature1", "feature2"],
  "category2": ["feature3"]
}
```

**Response**: Filtered features from specified categories

### 3. Write/Update Features
**Endpoint**: `POST /items/{identifier}`

**Parameters**:
- `identifier` (path): User/account identifier
- `table_type` (query, optional): `bright_uid` or `account_id` (default: `bright_uid`)

**Request Body** (Simplified Format):
```json
{
  "category1": {
    "feature1": "value1",
    "feature2": 123.45
  },
  "category2": {
    "feature3": true
  }
}
```

**Request Body** (Full Schema Format):
```json
{
  "category1": {
    "data": {
      "feature1": "value1",
      "feature2": 123.45
    },
    "metadata": {
      "created_at": "2025-10-06T06:30:00",
      "updated_at": "2025-10-06T06:30:00",
      "source": "api",
      "compute_id": "batch_job_001",
      "ttl": 86400
    }
  }
}
```

---

## Metrics System

### StatsD Metrics Overview
The system uses StatsD protocol for real-time metrics collection. All metrics are prefixed with `feature_store.`

### Metric Types

#### 1. Counters
Track the number of events/operations:

**Read Operations**:
- `feature_store.read.single_item.success` - Successful single item reads
- `feature_store.read.single_item.not_found` - Items not found
- `feature_store.read.single_item.error` - Read errors
- `feature_store.read.multi_category.success` - Successful multi-category reads
- `feature_store.read.multi_category.not_found` - No items found for mapping
- `feature_store.read.multi_category.error` - Multi-category read errors

**Write Operations**:
- `feature_store.write.multi_category.success` - Successful multi-category writes
- `feature_store.write.multi_category.error` - Write errors

**DynamoDB Operations**:
- `feature_store.dynamodb.get_item.found` - Items found in DynamoDB
- `feature_store.dynamodb.get_item.not_found` - Items not found in DynamoDB
- `feature_store.dynamodb.get_item.success` - Successful DynamoDB reads
- `feature_store.dynamodb.get_item.error` - DynamoDB read errors
- `feature_store.dynamodb.put_item.success` - Successful DynamoDB writes

#### 2. Gauges
Track current values:

- `feature_store.dynamodb.put_item.feature_count` - Number of features written per category

#### 3. Timers
Track operation duration in milliseconds:

- `feature_store.read.single_item.duration` - Single item read duration
- `feature_store.read.multi_category.duration` - Multi-category read duration
- `feature_store.write.multi_category.duration` - Multi-category write duration
- `feature_store.dynamodb.get_item.duration` - DynamoDB read duration
- `feature_store.dynamodb.put_item.duration` - DynamoDB write duration

### Metric Tags
Metrics include contextual tags for better analysis:

**Common Tags**:
- `identifier`: User/account identifier
- `category`: Feature category
- `table_type`: `bright_uid` or `account_id`
- `error_type`: Error classification
- `categories_count`: Number of categories processed

**Example Metric Names**:
```
feature_store.read.single_item.success,identifier=user123,category=trans_features,table_type=bright_uid
feature_store.dynamodb.put_item.feature_count,category=trans_features,table_type=bright_uid
feature_store.read.single_item.duration,identifier=user123,category=trans_features,table_type=bright_uid
```

---

## Request/Response Examples

### Example 1: Read Single Category (Default Table)
```bash
curl "http://127.0.0.1:8000/get/item/user123/trans_features"
```

**Response**:
```json
{
  "bright_uid": "user123",
  "category": "trans_features",
  "features": {
    "data": {
      "avg_credit_30d": 99.9,
      "num_of_r01": 7
    },
    "metadata": {
      "created_at": "2025-10-06T06:26:34.300154",
      "updated_at": "2025-10-06T06:26:34.300154",
      "source": "api",
      "compute_id": "None",
      "ttl": "None"
    }
  }
}
```

### Example 2: Read with Table Type
```bash
curl "http://127.0.0.1:8000/get/item/user123/trans_features?table_type=bright_uid"
```

### Example 3: Filtered Multi-Category Read
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
      "features": {
        "data": {
          "avg_credit_30d": 99.9
        },
        "metadata": {
          "created_at": "2025-10-06T06:26:34.300154",
          "source": "api",
          "updated_at": "2025-10-06T06:26:34.300154",
          "ttl": "None",
          "compute_id": "None"
        }
      },
      "category": "trans_features"
    },
    "balance_features": {
      "bright_uid": "user123",
      "features": {
        "data": {
          "avg_30d_bal": 2000.0
        },
        "metadata": {
          "created_at": "2025-10-06T06:26:34.568712",
          "source": "api",
          "updated_at": "2025-10-06T06:26:34.568712",
          "ttl": "None",
          "compute_id": "None"
        }
      },
      "category": "balance_features"
    }
  },
  "missing_categories": []
}
```

### Example 4: Write with Simplified Format
```bash
curl -X POST "http://127.0.0.1:8000/items/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{
    "trans_features": {
      "avg_credit_30d": 150.5,
      "num_transactions": 25
    },
    "balance_features": {
      "avg_30d_bal": 3000.0,
      "credit_limit": 5000
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
    "trans_features": {
      "status": "replaced",
      "feature_count": 2
    },
    "balance_features": {
      "status": "replaced",
      "feature_count": 2
    }
  },
  "total_features": 4
}
```

### Example 5: Write with Full Schema Format
```bash
curl -X POST "http://127.0.0.1:8000/items/user123?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{
    "user_features": {
      "data": {
        "age": 28,
        "income": 75000
      },
      "metadata": {
        "created_at": "2025-10-06T06:30:00",
        "updated_at": "2025-10-06T06:30:00",
        "source": "ml_pipeline",
        "compute_id": "batch_job_001",
        "ttl": 86400
      }
    }
  }'
```

---

## Error Handling

### HTTP Status Codes

| Status Code | Description | Example Response |
|-------------|-------------|------------------|
| 200 | Success | `{"bright_uid": "...", "features": {...}}` |
| 400 | Bad Request | `{"detail": "table_type must be 'bright_uid' or 'account_id'"}` |
| 404 | Not Found | `{"detail": "Item not found"}` |
| 500 | Internal Server Error | `{"detail": "Internal server error"}` |

### Common Error Scenarios

#### 1. Invalid Table Type
```bash
curl "http://127.0.0.1:8000/get/item/user123/trans_features?table_type=invalid_table"
```
**Response**: `400 Bad Request`
```json
{
  "detail": "table_type must be 'bright_uid' or 'account_id'"
}
```

#### 2. Item Not Found
```bash
curl "http://127.0.0.1:8000/get/item/non-existent-user/trans_features"
```
**Response**: `404 Not Found`
```json
{
  "detail": "Item not found"
}
```

#### 3. Empty Request Body
```bash
curl -X POST "http://127.0.0.1:8000/get/item/user123" \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Response**: `400 Bad Request`
```json
{
  "detail": "Mapping body cannot be empty"
}
```

---

## Schema Documentation

### Feature Data Structure

#### Simplified Format (Auto-Metadata)
```json
{
  "category_name": {
    "feature1": "value1",
    "feature2": 123.45,
    "feature3": true
  }
}
```

#### Full Schema Format
```json
{
  "category_name": {
    "data": {
      "feature1": "value1",
      "feature2": 123.45,
      "feature3": true
    },
    "metadata": {
      "created_at": "2025-10-06T06:30:00",
      "updated_at": "2025-10-06T06:30:00",
      "source": "api",
      "compute_id": "batch_job_001",
      "ttl": 86400
    }
  }
}
```

### Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `created_at` | string (ISO 8601) | Yes | Creation timestamp |
| `updated_at` | string (ISO 8601) | Yes | Last update timestamp |
| `source` | string | Yes | Data source (e.g., "api", "ml_pipeline") |
| `compute_id` | string | No | Processing job identifier |
| `ttl` | integer | No | Time-to-live in seconds |

### Supported Data Types

- **String**: `"value"`
- **Number**: `123.45`
- **Boolean**: `true`/`false`
- **Array**: `["item1", "item2"]`
- **Object**: `{"nested": "value"}`

---

## Monitoring Setup

### StatsD Server Configuration

#### 1. Start StatsD Server
```bash
cd /path/to/feature-store
python3 statsd_server.py
```

#### 2. Environment Variables
```bash
export STATSD_HOST=localhost
export STATSD_PORT=8125
export STATSD_PREFIX=feature_store
```

### Metrics Dashboard Integration

#### Grafana Dashboard Queries

**Request Rate**:
```
rate(feature_store_read_single_item_success[5m])
```

**Error Rate**:
```
rate(feature_store_read_single_item_error[5m]) / rate(feature_store_read_single_item_success[5m])
```

**Response Time (95th percentile)**:
```
histogram_quantile(0.95, rate(feature_store_read_single_item_duration_bucket[5m]))
```

**Feature Count by Category**:
```
feature_store_dynamodb_put_item_feature_count
```

### Alerting Rules

#### High Error Rate
```
rate(feature_store_read_single_item_error[5m]) > 0.1
```

#### High Response Time
```
histogram_quantile(0.95, rate(feature_store_read_single_item_duration_bucket[5m])) > 1000
```

#### Low Success Rate
```
rate(feature_store_read_single_item_success[5m]) / (rate(feature_store_read_single_item_success[5m]) + rate(feature_store_read_single_item_error[5m])) < 0.95
```

---

## Best Practices

### 1. Request Optimization
- Use filtered reads to reduce data transfer
- Batch multiple categories in single requests
- Choose appropriate table type for your use case

### 2. Error Handling
- Always check HTTP status codes
- Implement retry logic for transient errors
- Log error details for debugging

### 3. Monitoring
- Set up alerts for error rates > 5%
- Monitor response times (target: < 500ms)
- Track feature count trends
- Monitor table-specific metrics

### 4. Data Management
- Use TTL for temporary features
- Include meaningful source and compute_id
- Regular cleanup of expired features

---

## Troubleshooting

### Common Issues

#### 1. Table Not Found Error
**Error**: `ResourceNotFoundException`
**Solution**: Ensure the table exists in DynamoDB and table name is correct

#### 2. Invalid Table Type
**Error**: `table_type must be 'bright_uid' or 'account_id'`
**Solution**: Use valid table_type parameter

#### 3. High Response Times
**Symptoms**: Metrics show duration > 1000ms
**Solutions**:
- Check DynamoDB performance
- Optimize request patterns
- Consider caching

#### 4. Missing Features
**Symptoms**: Empty feature data in responses
**Solutions**:
- Verify feature names in requests
- Check data exists in DynamoDB
- Validate category names

---

## API Versioning

Current Version: `v1`
- Base URL: `http://127.0.0.1:8000`
- All endpoints are version-agnostic
- Backward compatibility maintained for schema changes

---

## Support

For issues or questions:
1. Check the metrics dashboard for system health
2. Review error logs for specific failures
3. Validate request format against documentation
4. Test with simplified requests first
