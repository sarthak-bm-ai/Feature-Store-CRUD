"""
Business logic flows for feature operations.
Separates business logic from API routes for clean architecture.
"""
from typing import Dict, List, Optional, Tuple, Any
from components.features import crud
from core.metrics import metrics, MetricNames
from core.logging_config import get_logger
from core.kafka_publisher import publish_feature_availability_event

# Configure logger
logger = get_logger("feature_flows")

class FeatureFlows:
    """Business logic flows for feature operations."""
    
    @staticmethod
    def get_single_category_flow(entity_value: str, category: str, entity_type: str) -> Dict:
        """
        Flow for getting a single category's features.
        
        Args:
            entity_value: User/account identifier
            category: Feature category
            entity_type: Entity type (bright_uid or account_pid)
            
        Returns:
            Dict containing the item data
            
        Raises:
            ValueError: If item not found
        """
        logger.info(f"Getting single category: {entity_value}/{category} from {entity_type}")
        
        # Get item from database
        item = crud.get_item(entity_value, category, entity_type)
        
        if not item:
            logger.warning(f"Item not found: {entity_value}/{category}")
            metrics.increment_counter(
                f"{MetricNames.READ_SINGLE_ITEM}.not_found",
                tags={"entity_value": entity_value, "category": category, "entity_type": entity_type}
            )
            raise ValueError(f"Item not found: {entity_value}/{category}")
        
        # Record success metrics
        metrics.increment_counter(
            f"{MetricNames.READ_SINGLE_ITEM}.success",
            tags={"entity_value": entity_value, "category": category, "entity_type": entity_type}
        )
        
        logger.info(f"Successfully retrieved category: {entity_value}/{category}")
        return item
    
    @staticmethod
    def get_multiple_categories_flow(entity_value: str, mapping: Dict[str, List[str]], entity_type: str) -> Dict:
        """
        Flow for getting multiple categories with optional filtering.
        
        Args:
            entity_value: User/account identifier
            mapping: Category to features mapping for filtering
            entity_type: Entity type (bright_uid or account_pid)
            
        Returns:
            Dict containing results and unavailable_feature_categories
            
        Raises:
            ValueError: If no items found
        """
        logger.info(f"Getting multiple categories for: {entity_value} from {entity_type}")
        
        if not mapping:
            logger.error("Empty mapping provided")
            metrics.increment_counter(
                f"{MetricNames.READ_MULTI_CATEGORY}.error",
                tags={"error_type": "empty_mapping", "entity_type": entity_type}
            )
            raise ValueError("Mapping body cannot be empty")
        
        results: Dict[str, dict] = {}
        missing: List[str] = []
        
        # Process each category in the mapping
        for category, features in mapping.items():
            logger.debug(f"Processing category: {category} with features: {features}")
            
            item = crud.get_item(entity_value, category, entity_type)
            if not item:
                missing.append(category)
                logger.warning(f"Category not found: {category}")
                continue
            
            # Apply filtering if features specified (skip if wildcard)
            if features and "*" not in features:
                item = FeatureFlows._filter_features(item, set(features))
                logger.debug(f"Applied filtering to {category}: {features}")
            elif "*" in features:
                logger.debug(f"Wildcard pattern detected for {category} - returning all features")
            
            results[category] = item
        
        if not results:
            logger.warning(f"No items found for entity_value: {entity_value}")
            metrics.increment_counter(
                f"{MetricNames.READ_MULTI_CATEGORY}.not_found",
                tags={"entity_value": entity_value, "entity_type": entity_type}
            )
            raise ValueError(f"No items found for entity_value '{entity_value}' with provided mapping")
        
        # Record success metrics
        metrics.increment_counter(
            f"{MetricNames.READ_MULTI_CATEGORY}.success",
            tags={"entity_value": entity_value, "entity_type": entity_type}
        )
        
        logger.info(f"Successfully retrieved {len(results)} categories for: {entity_value}")
        return {
            "entity_value": entity_value,
            "entity_type": entity_type,
            "items": results,
            "unavailable_feature_categories": missing
        }
    
    @staticmethod
    def upsert_category_flow(entity_value: str, category: str, features: Dict[str, Any], entity_type: str, compute_id: Optional[str] = None) -> Dict:
        """
        Flow for upserting a single category's features with automatic meta handling.
        
        Args:
            entity_value: User/account identifier
            category: Feature category
            features: Features data dictionary
            entity_type: Entity type (bright_uid or account_pid)
            compute_id: Optional ID of the compute job that generated the features
            
        Returns:
            Dict containing operation results
            
        Raises:
            ValueError: If validation fails
        """
        logger.info(f"Upserting category '{category}' for: {entity_value} to {entity_type} with compute_id: {compute_id}")
        
        if not features:
            logger.error("Empty features provided")
            metrics.increment_counter(
                f"{MetricNames.WRITE_SINGLE_CATEGORY}.error",
                tags={"error_type": "empty_features", "entity_type": entity_type, "category": category}
            )
            raise ValueError("Features cannot be empty")
        
        # Upsert with automatic meta handling, including compute_id
        crud.upsert_item_with_meta(entity_value, category, features, entity_type, compute_id)
        
        # Publish Kafka event after successful upsert
        try:
            feature_names = list(features.keys())
            success = publish_feature_availability_event(
                entity_type=entity_type,
                entity_value=entity_value,
                category=category,
                features=feature_names
            )
            if success:
                logger.info(f"Published Kafka event for {entity_type}:{entity_value} category: {category}")
            else:
                logger.warning(f"Failed to publish Kafka event for {entity_type}:{entity_value} category: {category}")
        except Exception as e:
            logger.error(f"Kafka event publishing failed for {category}: {e}")
            # Don't fail the upsert operation if Kafka fails
        
        # Record success metrics
        metrics.increment_counter(
            f"{MetricNames.WRITE_SINGLE_CATEGORY}.success",
            tags={"entity_value": entity_value, "entity_type": entity_type, "category": category}
        )
        
        feature_count = len(features)
        logger.info(f"Successfully upserted {feature_count} features for category '{category}' for: {entity_value}")
        
        return {
            "message": "Category written successfully (full replace)",
            "entity_value": entity_value,
            "entity_type": entity_type,
            "category": category,
            "feature_count": feature_count
        }
    
    @staticmethod
    def _filter_features(item: dict, feature_keys: set) -> dict:
        """
        Filter features in the new schema (data.meta structure).
        
        Args:
            item: Item containing features
            feature_keys: Set of feature keys to keep
            
        Returns:
            Filtered item with only specified features
        """
        if not feature_keys or "features" not in item:
            return item
        
        filtered = dict(item)
        features = filtered.get("features", {})
        
        if isinstance(features, dict) and "data" in features:
            filtered_data = {k: v for k, v in features["data"].items() if k in feature_keys}
            filtered["features"]["data"] = filtered_data
            logger.debug(f"Filtered features: {list(filtered_data.keys())}")
        
        return filtered
