# Account ID to Account PID Renaming

**Date**: October 16, 2025  
**Status**: ✅ Complete  
**Tests**: 117/117 passing (100%)

---

## Summary

Renamed all references from `account_id`/`account_uid` to `account_pid` throughout the entire codebase for consistency and clarity. The second DynamoDB table now consistently uses `account_pid` as the partition key and entity type identifier.

---

## Changes Made

### 1. Models (`components/features/models.py`)
- **Field**: `account_id` → `account_pid` in `Item` model
- **Validation**: Updated entity_type validation to accept `"account_pid"` instead of `"account_id"`
- **Examples**: Updated HealthResponse example to show `["bright_uid", "account_pid"]`

**Before**:
```python
class Item(BaseModel):
    bright_uid: Optional[str] = None
    account_id: Optional[str] = None  # OLD
    
# Validation
if v['entity_type'] not in ['bright_uid', 'account_id']:  # OLD
```

**After**:
```python
class Item(BaseModel):
    bright_uid: Optional[str] = None
    account_pid: Optional[str] = None  # NEW
    
# Validation
if v['entity_type'] not in ['bright_uid', 'account_pid']:  # NEW
```

---

### 2. Settings (`core/settings.py`)
- **Environment Variable**: `TABLE_NAME_ACCOUNT_ID` → `TABLE_NAME_ACCOUNT_PID`
- **Attribute**: `self.TABLE_NAME_ACCOUNT_ID` → `self.TABLE_NAME_ACCOUNT_PID`
- **get_table_name()**: Updated condition from `"account_id"` → `"account_pid"`

**Before**:
```python
self.TABLE_NAME_ACCOUNT_ID = os.getenv("TABLE_NAME_ACCOUNT_ID", "account_feature_store")

def get_table_name(self, table_type: str) -> str:
    if table_type == "account_id":
        return self.TABLE_NAME_ACCOUNT_ID
```

**After**:
```python
self.TABLE_NAME_ACCOUNT_PID = os.getenv("TABLE_NAME_ACCOUNT_PID", "account_feature_store")

def get_table_name(self, table_type: str) -> str:
    if table_type == "account_pid":
        return self.TABLE_NAME_ACCOUNT_PID
```

---

### 3. Config (`core/config.py`)
- **get_table()**: Updated condition from `"account_id"` → `"account_pid"`
- **get_all_tables()**: Updated loop to use `"account_pid"` instead of `"account_id"`
- **TABLES dict**: Updated key from `"account_id"` → `"account_pid"`

**Before**:
```python
elif table_type == "account_id":
    table_name = settings.TABLE_NAME_ACCOUNT_ID

for table_type in ["bright_uid", "account_id"]:
    
TABLES = {
    "bright_uid": lambda: get_table("bright_uid"),
    "account_id": lambda: get_table("account_id")
}
```

**After**:
```python
elif table_type == "account_pid":
    table_name = settings.TABLE_NAME_ACCOUNT_PID

for table_type in ["bright_uid", "account_pid"]:
    
TABLES = {
    "bright_uid": lambda: get_table("bright_uid"),
    "account_pid": lambda: get_table("account_pid")
}
```

---

### 4. Routes (`api/v1/routes.py`)
- **Query parameter description**: Updated from `'account_id'` → `'account_pid'`

**Before**:
```python
entity_type: str = Query(default="bright_uid", description="Entity type: 'bright_uid' or 'account_id'")
```

**After**:
```python
entity_type: str = Query(default="bright_uid", description="Entity type: 'bright_uid' or 'account_pid'")
```

---

### 5. Controller (`components/features/controller.py`)
- **Docstring**: Updated comment from `(bright_uid or account_id)` → `(bright_uid or account_pid)`

---

### 6. Flows (`components/features/flows.py`)
- **Docstrings**: Updated all docstrings from `(bright_uid or account_id)` → `(bright_uid or account_pid)`
- **3 locations** updated

---

### 7. CRUD (`components/features/crud.py`)
- **Docstring**: Updated function docstring from `(bright_uid or account_id)` → `(bright_uid or account_pid)`

---

### 8. Kafka Publisher (`core/kafka_publisher.py`)
- **Docstrings**: Updated all docstrings from `(bright_uid/account_id)` → `(bright_uid/account_pid)`
- **3 locations** updated

---

### 9. Tests (`test/test_crud.py`)
- **Test name**: `test_get_item_account_uid` → `test_get_item_account_pid`
- **Test docstring**: Updated from `account_uid` → `account_pid`
- **Mock data**: Changed key from `'account_uid'` → `'account_pid'`
- **Function call**: Updated parameter from `'account_uid'` → `'account_pid'`
- **Assertion**: Changed from `result['account_uid']` → `result['account_pid']`

**Before**:
```python
def test_get_item_account_uid(self, mock_get_table):
    """Test getting item with account_uid"""
    mock_table.get_item.return_value = {
        'Item': {
            'account_uid': 'account-123',
            ...
        }
    }
    result = crud.get_item('account-123', 'd0_unauth_features', 'account_uid')
    assert result['account_uid'] == 'account-123'
```

**After**:
```python
def test_get_item_account_pid(self, mock_get_table):
    """Test getting item with account_pid"""
    mock_table.get_item.return_value = {
        'Item': {
            'account_pid': 'account-123',
            ...
        }
    }
    result = crud.get_item('account-123', 'd0_unauth_features', 'account_pid')
    assert result['account_pid'] == 'account-123'
```

---

## Files Modified

### Core Code Files (9 files):
1. `components/features/models.py`
2. `components/features/controller.py`
3. `components/features/flows.py`
4. `components/features/crud.py`
5. `api/v1/routes.py`
6. `core/settings.py`
7. `core/config.py`
8. `core/kafka_publisher.py`
9. `test/test_crud.py`

### Documentation Files (Not Updated):
Documentation files like README.md, API_DOCUMENTATION.md, etc., still contain `account_id` references and should be updated if needed for end-user documentation.

---

## Environment Variables

### Old:
```bash
TABLE_NAME_ACCOUNT_ID=account_feature_store
```

### New:
```bash
TABLE_NAME_ACCOUNT_PID=account_feature_store
```

**Note**: If you have `.env` files or deployment configurations, update the environment variable name from `TABLE_NAME_ACCOUNT_ID` to `TABLE_NAME_ACCOUNT_PID`.

---

## API Usage Examples

### Before:
```json
{
  "data": {
    "entity_type": "account_id",
    "entity_value": "account-123",
    ...
  }
}
```

```bash
GET /api/v1/get/item/account-123/d0_unauth_features?entity_type=account_id
```

### After:
```json
{
  "data": {
    "entity_type": "account_pid",
    "entity_value": "account-123",
    ...
  }
}
```

```bash
GET /api/v1/get/item/account-123/d0_unauth_features?entity_type=account_pid
```

---

## DynamoDB Table Structure

The partition key name in DynamoDB tables should be:
- **Table 1**: `bright_uid` (user features)
- **Table 2**: `account_pid` (account features) - **previously `account_id` or `account_uid`**

Both tables use `category` as the sort key.

---

## Benefits

1. **Consistency**: Single naming convention (`account_pid`) used everywhere
2. **Clarity**: No confusion between `account_id` vs `account_uid`
3. **Standards**: `pid` (Partner ID) is a clearer identifier for account-level data
4. **Maintainability**: Easier to search and refactor with consistent naming

---

## Test Results

```
✅ 117/117 tests passing (100%)
⚡ Execution time: ~1.2 seconds
📝 All core functionality verified
```

---

## Migration Checklist

If deploying this change:

- [ ] Update environment variables: `TABLE_NAME_ACCOUNT_ID` → `TABLE_NAME_ACCOUNT_PID`
- [ ] Update API documentation
- [ ] Notify API consumers of the entity_type value change
- [ ] Update client SDKs or examples
- [ ] Update monitoring/alerting (if filtering by entity_type)
- [ ] Update any hardcoded references in deployment scripts

---

## Summary

✅ **Complete**: All `account_id`/`account_uid` references renamed to `account_pid`  
✅ **Tests Passing**: 117/117 (100%)  
✅ **Backward Compatibility**: Breaking change for API consumers using `entity_type: "account_id"`  
✅ **Environment Variables**: Renamed `TABLE_NAME_ACCOUNT_ID` → `TABLE_NAME_ACCOUNT_PID`  
✅ **Code Consistency**: Single naming convention throughout codebase  

**Note**: This is a **breaking change** for API consumers. They must update their requests to use `"account_pid"` instead of `"account_id"` for the `entity_type` field.


