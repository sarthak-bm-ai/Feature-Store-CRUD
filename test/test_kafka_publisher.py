"""
Unit tests for Kafka publisher
"""
import pytest
from unittest.mock import MagicMock, patch, Mock
import json

from core.kafka_publisher import FeatureEventPublisher, publish_feature_availability_event


class TestFeatureEventPublisher:
    """Tests for FeatureEventPublisher class"""
    
    @patch('core.kafka_publisher.AvroProducer')
    @patch('core.kafka_publisher.FeatureEventPublisher._load_avro_schema')
    def test_publisher_initialization(self, mock_load_schema, mock_producer_class):
        """Test publisher initializes correctly"""
        mock_schema = MagicMock()
        mock_load_schema.return_value = mock_schema
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer
        
        publisher = FeatureEventPublisher()
        
        assert publisher.avro_schema == mock_schema
        assert publisher.producer == mock_producer
    
    @patch('core.kafka_publisher.AvroProducer')
    @patch('core.kafka_publisher.FeatureEventPublisher._load_avro_schema')
    def test_load_avro_schema(self, mock_load_schema, mock_producer_class):
        """Test loading Avro schema from file"""
        mock_schema = MagicMock()
        mock_load_schema.return_value = mock_schema
        
        publisher = FeatureEventPublisher()
        
        mock_load_schema.assert_called_once()
    
    @patch('core.kafka_publisher.get_current_timestamp')
    @patch('core.kafka_publisher.AvroProducer')
    @patch('core.kafka_publisher.FeatureEventPublisher._load_avro_schema')
    def test_create_event_payload(self, mock_load_schema, mock_producer_class, mock_timestamp):
        """Test creating event payload"""
        mock_timestamp.return_value = "2025-10-14T12:34:56.789Z"
        mock_schema = MagicMock()
        mock_load_schema.return_value = mock_schema
        
        publisher = FeatureEventPublisher()
        
        payload = publisher._create_event_payload(
            entity_type="bright_uid",
            entity_value="test-123",
            category="d0_unauth_features",
            features=["credit_score", "age"],
            compute_id="compute-123"
        )
        
        assert payload['event_type'] == 'feature_available'
        assert payload['entity_type'] == 'bright_uid'
        assert payload['entity_id'] == 'test-123'
        assert payload['resource_name'] == 'd0_unauth_features'
        assert payload['features'] == ["credit_score", "age"]
        assert payload['compute_id'] == "compute-123"
        assert 'event_id' in payload
        assert 'timestamp' in payload
    
    @patch('core.kafka_publisher.get_current_timestamp')
    @patch('core.kafka_publisher.AvroProducer')
    @patch('core.kafka_publisher.FeatureEventPublisher._load_avro_schema')
    def test_create_event_payload_without_compute_id(self, mock_load_schema, mock_producer_class, mock_timestamp):
        """Test creating event payload without compute_id"""
        mock_timestamp.return_value = "2025-10-14T12:34:56.789Z"
        mock_schema = MagicMock()
        mock_load_schema.return_value = mock_schema
        
        publisher = FeatureEventPublisher()
        
        payload = publisher._create_event_payload(
            entity_type="bright_uid",
            entity_value="test-123",
            category="d0_unauth_features",
            features=["credit_score"]
        )
        
        # Should generate a compute_id if not provided
        assert 'compute_id' in payload
        assert payload['compute_id'] is not None
    
    @patch('core.kafka_publisher.AvroProducer')
    @patch('core.kafka_publisher.FeatureEventPublisher._load_avro_schema')
    def test_publish_success(self, mock_load_schema, mock_producer_class):
        """Test successful event publishing"""
        mock_schema = MagicMock()
        mock_load_schema.return_value = mock_schema
        mock_producer = MagicMock()
        mock_producer.produce.return_value = None
        mock_producer.flush.return_value = 0  # 0 messages remaining
        mock_producer_class.return_value = mock_producer
        
        publisher = FeatureEventPublisher()
        
        result = publisher.publish_feature_event(
            entity_type="bright_uid",
            entity_value="test-123",
            category="d0_unauth_features",
            features=["credit_score"]
        )
        
        assert result is True
        mock_producer.produce.assert_called_once()
        mock_producer.flush.assert_called()
    
    @patch('core.kafka_publisher.AvroProducer')
    @patch('core.kafka_publisher.FeatureEventPublisher._load_avro_schema')
    def test_publish_with_producer_exception(self, mock_load_schema, mock_producer_class):
        """Test publishing with producer exception"""
        mock_schema = MagicMock()
        mock_load_schema.return_value = mock_schema
        mock_producer = MagicMock()
        mock_producer.produce.side_effect = Exception("Kafka connection failed")
        mock_producer_class.return_value = mock_producer
        
        publisher = FeatureEventPublisher()
        
        result = publisher.publish_feature_event(
            entity_type="bright_uid",
            entity_value="test-123",
            category="d0_unauth_features",
            features=["credit_score"]
        )
        
        assert result is False
    
    @patch('core.kafka_publisher.AvroProducer')
    @patch('core.kafka_publisher.FeatureEventPublisher._load_avro_schema')
    def test_close_producer(self, mock_load_schema, mock_producer_class):
        """Test closing producer"""
        mock_schema = MagicMock()
        mock_load_schema.return_value = mock_schema
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer
        
        publisher = FeatureEventPublisher()
        publisher.close()
        
        mock_producer.flush.assert_called_once()


class TestPublishFeatureAvailabilityEvent:
    """Tests for publish_feature_availability_event function"""
    
    @patch('core.kafka_publisher._get_publisher')
    def test_publish_feature_availability_success(self, mock_get_publisher):
        """Test publishing feature availability event"""
        mock_publisher = MagicMock()
        mock_publisher.publish_feature_event.return_value = True
        mock_get_publisher.return_value = mock_publisher
        
        result = publish_feature_availability_event(
            entity_type="bright_uid",
            entity_value="test-123",
            category="d0_unauth_features",
            features=["credit_score", "age"]
        )
        
        assert result is True
        # Function uses positional args, not keyword args
        mock_publisher.publish_feature_event.assert_called_once_with(
            "bright_uid",
            "test-123",
            "d0_unauth_features",
            ["credit_score", "age"],
            None
        )
    
    @patch('core.kafka_publisher._get_publisher')
    def test_publish_feature_availability_with_compute_id(self, mock_get_publisher):
        """Test publishing with compute_id"""
        mock_publisher = MagicMock()
        mock_publisher.publish_feature_event.return_value = True
        mock_get_publisher.return_value = mock_publisher
        
        result = publish_feature_availability_event(
            entity_type="bright_uid",
            entity_value="test-123",
            category="d0_unauth_features",
            features=["credit_score"],
            compute_id="compute-123"
        )
        
        assert result is True
        # Function uses positional args
        call_args = mock_publisher.publish_feature_event.call_args
        assert call_args[0][4] == "compute-123"  # 5th positional arg
    
    @patch('core.kafka_publisher._get_publisher')
    def test_publish_feature_availability_failure(self, mock_get_publisher):
        """Test publishing failure"""
        mock_publisher = MagicMock()
        mock_publisher.publish_feature_event.return_value = False
        mock_get_publisher.return_value = mock_publisher
        
        result = publish_feature_availability_event(
            entity_type="bright_uid",
            entity_value="test-123",
            category="d0_unauth_features",
            features=["credit_score"]
        )
        
        assert result is False


class TestAvroSchema:
    """Tests for Avro schema validation"""
    
    def test_avro_schema_structure(self):
        """Test that Avro schema file exists and has correct structure"""
        import os
        schema_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'schemas',
            'feature_trigger.avsc'
        )
        
        assert os.path.exists(schema_path), "Avro schema file should exist"
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        assert schema['type'] == 'record'
        assert schema['name'] == 'FeatureAvailabilityEvent'
        assert 'fields' in schema
        
        # Check required fields
        field_names = [field['name'] for field in schema['fields']]
        required_fields = [
            'event_id', 'event_type', 'timestamp',
            'entity_type', 'entity_id', 'resource_type',
            'resource_name', 'compute_id', 'features'
        ]
        for field in required_fields:
            assert field in field_names, f"Field {field} should be in schema"


