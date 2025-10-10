"""
Business logic flows for feature operations.
Separates business logic from API routes for clean architecture.
"""
from typing import Dict, List, Optional, Tuple
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
            entity_type: Entity type (bright_uid or account_id)
            
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
            entity_type: Entity type (bright_uid or account_id)
            
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
    def upsert_features_flow(entity_value: str, items: Dict[str, Dict], entity_type: str) -> Dict:
        """
        Flow for upserting features with automatic metadata handling.
        
        Args:
            entity_value: User/account identifier
            items: Features data organized by category
            entity_type: Entity type (bright_uid or account_id)
            
        Returns:
            Dict containing operation results
            
        Raises:
            ValueError: If validation fails
        """
        logger.info(f"Upserting features for: {entity_value} to {entity_type}")
        
        if not items:
            logger.error("Empty items provided")
            metrics.increment_counter(
                f"{MetricNames.WRITE_MULTI_CATEGORY}.error",
                tags={"error_type": "empty_body", "entity_type": entity_type}
            )
            raise ValueError("Request body cannot be empty")
        
        results: Dict[str, dict] = {}
        total_features = 0
        
        # Process each category
        for category, features in items.items():
            logger.debug(f"Processing category: {category} with {len(features)} features")
            
            # Validate features data
            if not isinstance(features, dict):
                logger.error(f"Invalid features type for category: {category}")
                raise ValueError(f"Features for category '{category}' must be a valid object/dictionary")
            
            # Upsert with automatic metadata handling
            crud.upsert_item_with_metadata(entity_value, category, features, entity_type)
            
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
            
            total_features += len(features)
            results[category] = {
                "status": "replaced",
                "feature_count": len(features)
            }
            
            logger.debug(f"Successfully processed category: {category}")
        
        # Record success metrics
        metrics.increment_counter(
            f"{MetricNames.WRITE_MULTI_CATEGORY}.success",
            tags={"entity_value": entity_value, "entity_type": entity_type, "categories_count": str(len(items))}
        )
        
        logger.info(f"Successfully upserted {total_features} features across {len(items)} categories for: {entity_value}")
        return {
            "message": "Items written successfully (full replace per category)",
            "entity_value": entity_value,
            "entity_type": entity_type,
            "results": results,
            "total_features": total_features
        }
    
    @staticmethod
    def _filter_features(item: dict, feature_keys: set) -> dict:
        """
        Filter features in the new schema (data.metadata structure).
        
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
