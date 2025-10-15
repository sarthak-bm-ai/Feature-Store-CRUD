# Feature Store Unit Tests

Comprehensive unit test suite for the Feature Store CRUD API.

## Test Structure

```
test/
├── __init__.py              # Package initialization
├── conftest.py              # Pytest fixtures and configuration
├── pytest.ini               # Pytest settings
├── README.md                # This file
├── test_models.py           # Pydantic model tests
├── test_services.py         # Service layer tests
├── test_crud.py             # CRUD operation tests
├── test_flows.py            # Flow layer tests
├── test_controller.py       # Controller layer tests
├── test_routes.py           # API route tests
├── test_timestamp_utils.py  # Timestamp utility tests
└── test_kafka_publisher.py  # Kafka integration tests
```

## Prerequisites

Install test dependencies:

```bash
pip install pytest pytest-cov pytest-mock
```

## Running Tests

### Run All Tests

```bash
# From project root
pytest

# Or from test directory
cd test
pytest
```

### Run Specific Test File

```bash
pytest test/test_models.py
pytest test/test_services.py
pytest test/test_crud.py
```

### Run Specific Test Class

```bash
pytest test/test_models.py::TestFeatureMeta
pytest test/test_services.py::TestValidateRequestStructure
```

### Run Specific Test

```bash
pytest test/test_models.py::TestFeatureMeta::test_feature_meta_creation
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only CRUD tests
pytest -m crud

# Run only model tests
pytest -m models
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=components --cov=core --cov=api --cov-report=html --cov-report=term-missing

# View coverage report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

### Run and Show Print Statements

```bash
pytest -s
```

### Run and Stop on First Failure

```bash
pytest -x
```

### Run Only Failed Tests from Last Run

```bash
pytest --lf
```

## Test Coverage

### Models (`test_models.py`)
- ✅ FeatureMeta validation
- ✅ Features model structure
- ✅ RequestMeta validation
- ✅ WriteRequestMeta with source validation
- ✅ WriteRequest and ReadRequest validation
- ✅ Response models (WriteResponse, ReadResponse)
- ✅ HealthResponse and ErrorResponse
- ✅ Timestamp parsing and validation

### Services (`test_services.py`)
- ✅ Request structure validation
- ✅ Entity value sanitization
- ✅ Feature list to mapping conversion
- ✅ Wildcard pattern handling
- ✅ Category validation for writes
- ✅ Items validation
- ✅ Source validation
- ✅ Category extraction from feature lists

### CRUD (`test_crud.py`)
- ✅ Get item operations (found/not found)
- ✅ Upsert operations (new/existing items)
- ✅ Float to Decimal conversion
- ✅ DynamoDB serialization/deserialization
- ✅ Error handling (ClientError)
- ✅ Multi-entity type support (bright_uid/account_uid)

### Flows (`test_flows.py`)
- ✅ Get multiple categories flow
- ✅ Wildcard feature retrieval
- ✅ Feature filtering
- ✅ Upsert features flow
- ✅ Kafka event publishing integration
- ✅ Missing category handling
- ✅ Kafka failure resilience

### Controller (`test_controller.py`)
- ✅ Get multiple categories endpoint
- ✅ Upsert features endpoint
- ✅ Get single category endpoint
- ✅ Request validation
- ✅ Source validation
- ✅ Category validation
- ✅ Error propagation

### Routes (`test_routes.py`)
- ✅ Health check endpoint
- ✅ POST /get/items endpoint
- ✅ POST /items endpoint
- ✅ GET /get/item/{entity_value} endpoint
- ✅ Wildcard feature requests
- ✅ Error responses (404, 400, 422)
- ✅ CORS middleware

### Timestamp Utils (`test_timestamp_utils.py`)
- ✅ Current timestamp generation
- ✅ Timestamp formatting
- ✅ Timestamp parsing (multiple formats)
- ✅ Format validation
- ✅ Consistency enforcement
- ✅ Roundtrip conversions

### Kafka Publisher (`test_kafka_publisher.py`)
- ✅ Publisher initialization
- ✅ Avro schema loading
- ✅ Event payload creation
- ✅ Event publishing (success/failure)
- ✅ Producer error handling
- ✅ Schema structure validation

## Mocking Strategy

All tests use mocks to avoid external dependencies:

- **DynamoDB**: Mocked using `unittest.mock.MagicMock`
- **Kafka**: Mocked `AvroProducer` and event publishing
- **Timestamps**: Auto-mocked via `conftest.py` fixture for consistent testing
- **External APIs**: No external calls in unit tests

## Fixtures

Available fixtures (defined in `conftest.py`):

- `client`: FastAPI TestClient
- `mock_dynamodb_table`: Mocked DynamoDB table
- `mock_dynamodb_resource`: Mocked DynamoDB resource
- `sample_feature_data`: Sample feature dictionary
- `sample_write_request`: Sample write request payload
- `sample_read_request`: Sample read request payload
- `sample_dynamodb_item`: Sample DynamoDB item structure
- `sample_timestamp`: Fixed timestamp for testing
- `mock_kafka_producer`: Mocked Kafka producer
- `mock_get_current_timestamp`: Auto-applied timestamp mock

## Test Best Practices

1. **Isolation**: Each test is independent and doesn't affect others
2. **Mocking**: External dependencies are mocked to ensure fast, reliable tests
3. **Coverage**: Tests cover happy paths, edge cases, and error scenarios
4. **Naming**: Test names clearly describe what they test
5. **Assertions**: Clear, specific assertions for each test case

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=components --cov=core --cov=api \
           --cov-report=xml \
           --cov-report=term-missing
```

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running pytest from the project root:

```bash
cd /path/to/Feature-Store-CRUD
pytest
```

### Missing Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock
```

### DynamoDB Connection Errors

Unit tests should NOT connect to actual DynamoDB. If you see connection errors:
1. Check that mocks are properly applied
2. Verify `conftest.py` fixtures are being used

### Kafka Connection Errors

Unit tests should NOT connect to actual Kafka. If you see connection errors:
1. Check that `kafka_publisher` is properly mocked
2. Verify Avro producer mocks are in place

## Future Enhancements

- [ ] Integration tests with actual DynamoDB (LocalStack)
- [ ] Integration tests with actual Kafka (testcontainers)
- [ ] Performance tests
- [ ] Load tests
- [ ] End-to-end tests

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain > 80% code coverage
4. Update this README if adding new test files



