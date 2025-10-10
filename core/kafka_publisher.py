"""
Kafka publisher for feature availability events with Avro serialization.
Handles event publishing to Kafka with schema registry integration.
"""
import json
import uuid
import os
import avro.schema
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from confluent_kafka.avro import AvroProducer
from confluent_kafka.avro.serializer import SerializerError
from core.settings import settings
from core.logging_config import get_logger

logger = get_logger("kafka_publisher")

class FeatureEventPublisher:
    """Publisher for feature availability events to Kafka."""
    
    def __init__(self):
        """Initialize Kafka producer with Avro serialization."""
        self.producer = None
        self.topic_name = settings.TOPIC_NAME
        self.avro_schema = self._load_avro_schema()
        self._initialize_producer()
    
    def _load_avro_schema(self):
        """Load Avro schema from .avsc file and parse it."""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), '..', 'schemas', 'feature_trigger.avsc')
            with open(schema_path, 'r') as f:
                schema_dict = json.load(f)
            
            # Convert dict to JSON string and parse into Avro Schema object
            # This is required because AvroProducer expects an avro.schema.Schema object
            schema = avro.schema.parse(json.dumps(schema_dict))
            
            logger.info(f"Loaded and parsed Avro schema from {schema_path}")
            return schema
        except Exception as e:
            logger.error(f"Failed to load Avro schema: {e}")
            raise
    
    def _initialize_producer(self):
        """Initialize the Avro producer with schema registry."""
        try:
            producer_config = {
                'bootstrap.servers': settings.KAFKA_BROKER_URL,
                'schema.registry.url': settings.SCHEMA_REGISTRY,
                'client.id': 'feature-store-api',
                'acks': 'all',  # Wait for all replicas to acknowledge
                'retries': 3,
                'retry.backoff.ms': 100,
                'compression.type': 'snappy'
            }
            
            self.producer = AvroProducer(
                producer_config,
                default_value_schema=self.avro_schema
            )
            logger.info(f"Avro producer initialized for topic: {self.topic_name} with schema registry: {settings.SCHEMA_REGISTRY}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Avro producer: {e}")
            raise
    
    def _create_event_payload(self, entity_type: str, entity_value: str, 
                            category: str, features: List[str], 
                            compute_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create the event payload structure.
        
        Args:
            entity_type: Type of entity (bright_uid/account_id)
            entity_value: Entity identifier
            category: Feature category
            features: List of feature names
            compute_id: Optional compute ID
            
        Returns:
            Event payload dictionary
        """
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "feature_available",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entity_type": entity_type,
            "entity_id": entity_value,
            "resource_type": "feature",
            "resource_name": category,
            "compute_id": compute_id or str(uuid.uuid4()),
            "features": features
        }
    
    def publish_feature_event(self, entity_type: str, entity_value: str, 
                            category: str, features: List[str], 
                            compute_id: Optional[str] = None) -> bool:
        """
        Publish feature availability event to Kafka.
        
        Args:
            entity_type: Type of entity (bright_uid/account_id)
            entity_value: Entity identifier
            category: Feature category
            features: List of feature names
            compute_id: Optional compute ID
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            if not self.producer:
                logger.error("Kafka producer not initialized")
                return False
            
            # Create event payload
            event_payload = self._create_event_payload(
                entity_type, entity_value, category, features, compute_id
            )
            
            # Publish to Kafka with Avro serialization
            self.producer.produce(
                topic=self.topic_name,
                value=event_payload,
                callback=self._delivery_callback
            )
            
            # Flush to ensure message is sent
            self.producer.flush(timeout=10)
            
            logger.info(f"Published feature event for {entity_type}:{entity_value} category: {category}")
            logger.debug(f"Event payload: {json.dumps(event_payload, indent=2)}")
            
            return True
            
        except SerializerError as e:
            logger.error(f"Avro serialization error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to publish feature event: {e}")
            return False
    
    def _delivery_callback(self, err, msg):
        """Callback for message delivery confirmation."""
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
    
    def close(self):
        """Close the Kafka producer."""
        if self.producer:
            self.producer.flush()
            self.producer = None
            logger.info("Kafka producer closed")

# Global publisher instance
kafka_publisher = FeatureEventPublisher()

def publish_feature_availability_event(entity_type: str, entity_value: str, 
                                      category: str, features: List[str], 
                                      compute_id: Optional[str] = None) -> bool:
    """
    Convenience function to publish feature availability events.
    
    Args:
        entity_type: Type of entity (bright_uid/account_id)
        entity_value: Entity identifier
        category: Feature category
        features: List of feature names
        compute_id: Optional compute ID
        
    Returns:
        True if published successfully, False otherwise
    """
    return kafka_publisher.publish_feature_event(
        entity_type, entity_value, category, features, compute_id
    )
