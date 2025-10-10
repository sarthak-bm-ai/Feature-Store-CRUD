"""
Business logic flows for feature operations.
Separates business logic from API routes for clean architecture.
"""
from typing import Dict, List, Optional, Tuple
from components.features import crud
from core.metrics import metrics, MetricNames
from core.logging_config import get_logger

# Configure logger
logger = get_logger("feature_flows")

class FeatureFlows:
    """Business logic flows for feature operations."""
    
    @staticmethod
    def get_single_category_flow(identifier: str, category: str, table_type: str) -> Dict:
        """
        Flow for getting a single category's features.
        
        Args:
            identifier: User/account identifier
            category: Feature category
            table_type: Table type (bright_uid or account_id)
            
        Returns:
            Dict containing the item data
            
        Raises:
            ValueError: If item not found
        """
        logger.info(f"Getting single category: {identifier}/{category} from {table_type}")
        
        # Get item from database
        item = crud.get_item(identifier, category, table_type)
        
        if not item:
            logger.warning(f"Item not found: {identifier}/{category}")
            metrics.increment_counter(
                f"{MetricNames.READ_SINGLE_ITEM}.not_found",
                tags={"identifier": identifier, "category": category, "table_type": table_type}
            )
            raise ValueError(f"Item not found: {identifier}/{category}")
        
        # Record success metrics
        metrics.increment_counter(
            f"{MetricNames.READ_SINGLE_ITEM}.success",
            tags={"identifier": identifier, "category": category, "table_type": table_type}
        )
        
        logger.info(f"Successfully retrieved category: {identifier}/{category}")
        return item
    
    @staticmethod
    def get_multiple_categories_flow(identifier: str, mapping: Dict[str, List[str]], table_type: str) -> Dict:
        """
        Flow for getting multiple categories with optional filtering.
        
        Args:
            identifier: User/account identifier
            mapping: Category to features mapping for filtering
            table_type: Table type (bright_uid or account_id)
            
        Returns:
            Dict containing results and missing categories
            
        Raises:
            ValueError: If no items found
        """
        logger.info(f"Getting multiple categories for: {identifier} from {table_type}")
        
        if not mapping:
            logger.error("Empty mapping provided")
            metrics.increment_counter(
                f"{MetricNames.READ_MULTI_CATEGORY}.error",
                tags={"error_type": "empty_mapping", "table_type": table_type}
            )
            raise ValueError("Mapping body cannot be empty")
        
        results: Dict[str, dict] = {}
        missing: List[str] = []
        
        # Process each category in the mapping
        for category, features in mapping.items():
            logger.debug(f"Processing category: {category} with features: {features}")
            
            item = crud.get_item(identifier, category, table_type)
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
            logger.warning(f"No items found for identifier: {identifier}")
            metrics.increment_counter(
                f"{MetricNames.READ_MULTI_CATEGORY}.not_found",
                tags={"identifier": identifier, "table_type": table_type}
            )
            raise ValueError(f"No items found for identifier '{identifier}' with provided mapping")
        
        # Record success metrics
        metrics.increment_counter(
            f"{MetricNames.READ_MULTI_CATEGORY}.success",
            tags={"identifier": identifier, "table_type": table_type}
        )
        
        logger.info(f"Successfully retrieved {len(results)} categories for: {identifier}")
        return {
            "identifier": identifier,
            "table_type": table_type,
            "items": results,
            "missing_categories": missing
        }
    
    @staticmethod
    def upsert_features_flow(identifier: str, items: Dict[str, Dict], table_type: str) -> Dict:
        """
        Flow for upserting features with automatic metadata handling.
        
        Args:
            identifier: User/account identifier
            items: Features data organized by category
            table_type: Table type (bright_uid or account_id)
            
        Returns:
            Dict containing operation results
            
        Raises:
            ValueError: If validation fails
        """
        logger.info(f"Upserting features for: {identifier} to {table_type}")
        
        if not items:
            logger.error("Empty items provided")
            metrics.increment_counter(
                f"{MetricNames.WRITE_MULTI_CATEGORY}.error",
                tags={"error_type": "empty_body", "table_type": table_type}
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
            crud.upsert_item_with_metadata(identifier, category, features, table_type)
            
            total_features += len(features)
            results[category] = {
                "status": "replaced",
                "feature_count": len(features)
            }
            
            logger.debug(f"Successfully processed category: {category}")
        
        # Record success metrics
        metrics.increment_counter(
            f"{MetricNames.WRITE_MULTI_CATEGORY}.success",
            tags={"identifier": identifier, "table_type": table_type, "categories_count": str(len(items))}
        )
        
        logger.info(f"Successfully upserted {total_features} features across {len(items)} categories for: {identifier}")
        return {
            "message": "Items written successfully (full replace per category)",
            "identifier": identifier,
            "table_type": table_type,
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
