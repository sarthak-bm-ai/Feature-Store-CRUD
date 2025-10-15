"""
Pytest configuration and fixtures for Feature Store tests
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from decimal import Decimal

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now safe to import - Kafka publisher is lazy-loaded
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table"""
    table = MagicMock()
    table.get_item = MagicMock()
    table.put_item = MagicMock()
    table.table_name = "feature_store_bright_uid"
    return table


@pytest.fixture
def mock_dynamodb_resource():
    """Mock DynamoDB resource"""
    resource = MagicMock()
    return resource


@pytest.fixture
def sample_feature_data():
    """Sample feature data for testing"""
    return {
        "credit_score": 750,
        "debt_to_income_ratio": 0.35,
        "payment_history_score": 85.5,
        "account_age_months": 36
    }


@pytest.fixture
def sample_write_request():
    """Sample write request payload (single category)"""
    return {
        "meta": {
            "source": "prediction_service"
        },
        "data": {
            "entity_type": "bright_uid",
            "entity_value": "test-user-123",
            "category": "d0_unauth_features",
            "features": {
                "credit_score": 750,
                "debt_to_income_ratio": 0.35
            }
        }
    }


@pytest.fixture
def sample_read_request():
    """Sample read request payload"""
    return {
        "meta": {
            "source": "api"
        },
        "data": {
            "entity_type": "bright_uid",
            "entity_value": "test-user-123",
            "feature_list": [
                "d0_unauth_features:credit_score",
                "d0_unauth_features:debt_to_income_ratio"
            ]
        }
    }


@pytest.fixture
def sample_dynamodb_item():
    """Sample DynamoDB item structure"""
    return {
        "buid": "test-user-123",
        "d0_unauth_features": {
            "data": {
                "credit_score": Decimal("750"),
                "debt_to_income_ratio": Decimal("0.35")
            },
            "meta": {
                "created_at": "2025-10-14T12:34:56.789Z",
                "updated_at": "2025-10-14T12:34:56.789Z",
                "compute_id": None
            }
        }
    }


@pytest.fixture
def sample_timestamp():
    """Sample timestamp in ISO 8601 format"""
    return "2025-10-14T12:34:56.789Z"


@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer"""
    producer = MagicMock()
    producer.produce = MagicMock()
    producer.flush = MagicMock()
    producer.poll = MagicMock()
    return producer


@pytest.fixture(autouse=True)
def mock_get_current_timestamp():
    """Auto-mock timestamp generation for consistent testing"""
    with patch('core.timestamp_utils.get_current_timestamp') as mock:
        mock.return_value = "2025-10-14T12:34:56.789Z"
        yield mock


@pytest.fixture(autouse=True)
def mock_kafka_publisher():
    """Auto-mock Kafka publisher to prevent connection attempts during tests"""
    with patch('core.kafka_publisher._get_publisher') as mock:
        mock_publisher = MagicMock()
        mock_publisher.publish_feature_event.return_value = True
        mock.return_value = mock_publisher
        yield mock_publisher




