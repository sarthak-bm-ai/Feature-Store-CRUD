# DynamoDB Singleton Lock Bug Fix

## Issue Summary
The write API endpoint was hanging indefinitely on the first request when trying to initialize the DynamoDB connection. The application appeared to freeze when calling `get_table()` for the first time.

## Root Cause
The `DynamoDBSingleton` class had a critical bug in its lock implementation:

1. **Class-level lock**: The class defined a `_lock` attribute at the class level (line 16):
   ```python
   class DynamoDBSingleton:
       _instance = None
       _lock = threading.Lock()  # Class-level lock
   ```

2. **Missing instance-level lock**: The `__init__` method did NOT create an instance-level `_lock` attribute:
   ```python
   def __init__(self):
       if not self._initialized:
           self._dynamodb = None
           self._tables = {}
           # Missing: self._lock = threading.RLock()
   ```

3. **Lock conflict**: When `get_dynamodb_resource()` tried to acquire `self._lock`, it was using the class-level `threading.Lock()` (which is NOT reentrant), not an instance-level `threading.RLock()`.

4. **Deadlock**: The class-level lock used in `__new__()` for singleton creation was somehow interfering with the instance methods trying to use the same class-level lock, causing a deadlock situation.

## The Fix
Added an instance-level `RLock` in the `__init__` method:

```python
def __init__(self):
    if not self._initialized:
        self._lock = threading.RLock()  # Instance-level lock for resource initialization
        self._dynamodb = None
        self._tables = {}
        self._initialized = True
        logger.info("DynamoDB Singleton initialized")
```

### Why RLock?
- `threading.RLock()` (Reentrant Lock) allows the same thread to acquire the lock multiple times
- This is important because `get_table()` calls `get_dynamodb_resource()`, and both use the same lock
- With a regular `Lock()`, this would cause a deadlock when the same thread tries to acquire it twice

## Performance Impact
After the fix:
- **First request**: ~3.7 seconds (lazy initialization of DynamoDB and Kafka)
- **Subsequent requests**: ~0.8-0.95 seconds (resources already initialized)

## Files Changed
1. **`core/config.py`**:
   - Added `self._lock = threading.RLock()` in `__init__`
   - Removed debug logging added during troubleshooting

2. **`components/features/crud.py`**:
   - Removed debug logging added during troubleshooting

3. **`core/kafka_publisher.py`**:
   - Removed debug logging added during troubleshooting

## Testing
Tested with the following curl command:
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

**Results**:
- ✅ First request: 3.67s (successful, includes initialization)
- ✅ Second request: 0.82s (successful, fast)

## Key Learnings
1. **Always initialize instance-level locks in `__init__`** - Don't rely on class-level locks for instance methods
2. **Use `RLock` for reentrant scenarios** - When methods call each other and both need the lock
3. **Class-level vs instance-level attributes** - Be explicit about which attributes belong where
4. **Thread safety in singletons** - Singleton pattern with lazy initialization requires careful lock management

## Conclusion
The bug was caused by a missing instance-level lock initialization. The fix was simple: add `self._lock = threading.RLock()` in `__init__`. This ensures each singleton instance has its own lock that can be safely acquired multiple times by the same thread, preventing the deadlock situation that was causing the API to hang.

