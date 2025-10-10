"""
Service layer for feature operations.
Handles validation, business rules, and data transformation.
"""
from typing import Dict, List, Optional
from core.logging_config import get_logger

# Configure logger
logger = get_logger("feature_services")

class FeatureServices:
    """Service layer for feature operations."""
    
    @staticmethod
    def validate_table_type(table_type: str) -> None:
        """
        Validate table type parameter.
        
        Args:
            table_type: Table type to validate
            
        Raises:
            ValueError: If table type is invalid
        """
        valid_types = ["bright_uid", "account_id"]
        if table_type not in valid_types:
            logger.error(f"Invalid table type: {table_type}")
            raise ValueError(f"Invalid table_type '{table_type}'. Must be 'bright_uid' or 'account_id'")
        
        logger.debug(f"Table type validated: {table_type}")
    
    @staticmethod
    def validate_mapping(mapping: Dict[str, List[str]]) -> None:
        """
        Validate feature mapping for multi-category reads.
        
        Args:
            mapping: Feature mapping to validate
            
        Raises:
            ValueError: If mapping is invalid
        """
        if not mapping:
            logger.error("Empty mapping provided")
            raise ValueError("Mapping body cannot be empty")
        
        # Validate mapping structure
        for category, features in mapping.items():
            if not isinstance(category, str):
                logger.error(f"Invalid category type: {type(category)}")
                raise ValueError(f"Category must be a string, got {type(category)}")
            
            if not isinstance(features, list):
                logger.error(f"Invalid features type for category {category}: {type(features)}")
                raise ValueError(f"Features for category '{category}' must be a list")
            
            # Validate feature names are strings
            for feature in features:
                if not isinstance(feature, str):
                    logger.error(f"Invalid feature type in {category}: {type(feature)}")
                    raise ValueError(f"Feature names must be strings, got {type(feature)}")
        
        logger.debug(f"Mapping validated: {len(mapping)} categories")
    
    @staticmethod
    def validate_items(items: Dict[str, Dict]) -> None:
        """
        Validate items for upsert operations.
        
        Args:
            items: Items to validate
            
        Raises:
            ValueError: If items are invalid
        """
        if not items:
            logger.error("Empty items provided")
            raise ValueError("Request body cannot be empty")
        
        # Validate items structure
        for category, features in items.items():
            if not isinstance(category, str):
                logger.error(f"Invalid category type: {type(category)}")
                raise ValueError(f"Category must be a string, got {type(category)}")
            
            if not isinstance(features, dict):
                logger.error(f"Invalid features type for category {category}: {type(features)}")
                raise ValueError(f"Features for category '{category}' must be a valid object/dictionary")
            
            # Validate feature data types
            for feature_name, feature_value in features.items():
                if not isinstance(feature_name, str):
                    logger.error(f"Invalid feature name type in {category}: {type(feature_name)}")
                    raise ValueError(f"Feature names must be strings, got {type(feature_name)}")
                
                # Validate feature value types (basic validation)
                if feature_value is None:
                    logger.warning(f"Null feature value for {category}.{feature_name}")
                elif not isinstance(feature_value, (str, int, float, bool, list, dict)):
                    logger.warning(f"Unusual feature value type for {category}.{feature_name}: {type(feature_value)}")
        
        logger.debug(f"Items validated: {len(items)} categories")
    
    @staticmethod
    def sanitize_entity_value(entity_value: str) -> str:
        """
        Sanitize entity value for security.
        
        Args:
            entity_value: Entity value to sanitize
            
        Returns:
            Sanitized entity value
        """
        if not entity_value:
            logger.error("Empty entity value provided")
            raise ValueError("Entity value cannot be empty")
        
        if not isinstance(entity_value, str):
            logger.error(f"Invalid entity value type: {type(entity_value)}")
            raise ValueError(f"Entity value must be a string, got {type(entity_value)}")
        
        # Basic sanitization - remove potentially dangerous characters
        sanitized = entity_value.strip()
        
        # Check for reasonable length
        if len(sanitized) > 255:
            logger.warning(f"Very long entity value: {len(sanitized)} characters")
            sanitized = sanitized[:255]
        
        logger.debug(f"Entity value sanitized: {len(entity_value)} -> {len(sanitized)}")
        return sanitized
    
    @staticmethod
    def sanitize_category(category: str) -> str:
        """
        Sanitize category name for security.
        
        Args:
            category: Category to sanitize
            
        Returns:
            Sanitized category
        """
        if not category:
            logger.error("Empty category provided")
            raise ValueError("Category cannot be empty")
        
        if not isinstance(category, str):
            logger.error(f"Invalid category type: {type(category)}")
            raise ValueError(f"Category must be a string, got {type(category)}")
        
        # Basic sanitization
        sanitized = category.strip()
        
        # Check for reasonable length
        if len(sanitized) > 100:
            logger.warning(f"Very long category: {len(sanitized)} characters")
            sanitized = sanitized[:100]
        
        logger.debug(f"Category sanitized: {len(category)} -> {len(sanitized)}")
        return sanitized
    
    @staticmethod
    def validate_request_structure(request_data: Dict) -> tuple:
        """
        Validate and extract metadata and data from request.
        
        Args:
            request_data: Request data containing metadata and data
            
        Returns:
            Tuple of (metadata, data)
            
        Raises:
            ValueError: If request structure is invalid
        """
        if not request_data:
            logger.error("Empty request data provided")
            raise ValueError("Request body cannot be empty")
        
        # Validate top-level structure
        if "metadata" not in request_data:
            logger.error("Missing metadata in request")
            raise ValueError("Request must contain 'metadata' field")
        
        if "data" not in request_data:
            logger.error("Missing data in request")
            raise ValueError("Request must contain 'data' field")
        
        metadata = request_data["metadata"]
        data = request_data["data"]
        
        # Validate metadata structure
        if not isinstance(metadata, dict):
            logger.error(f"Invalid metadata type: {type(metadata)}")
            raise ValueError("Metadata must be a dictionary")
        
        # Validate data structure
        if not isinstance(data, dict):
            logger.error(f"Invalid data type: {type(data)}")
            raise ValueError("Data must be a dictionary")
        
        # Validate required data fields
        required_fields = ["entity_type", "entity_value", "feature_list"]
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                raise ValueError(f"Data must contain '{field}' field")
        
        logger.debug("Request structure validated successfully")
        return metadata, data
    
    @staticmethod
    def convert_feature_list_to_mapping(feature_list: List[str]) -> Dict[str, List[str]]:
        """
        Convert feature list to mapping format for read operations.
        Supports wildcard patterns like "category:*" to get all features of a category.
        
        Args:
            feature_list: List of features in format ["cat1:f1", "cat1:f2", "cat2:*"]
            
        Returns:
            Mapping in format {"cat1": ["f1", "f2"], "cat2": ["*"]}
        """
        if not feature_list:
            logger.error("Empty feature list provided")
            raise ValueError("Feature list cannot be empty")
        
        if not isinstance(feature_list, list):
            logger.error(f"Invalid feature list type: {type(feature_list)}")
            raise ValueError("Feature list must be a list")
        
        mapping = {}
        for feature in feature_list:
            if not isinstance(feature, str):
                logger.error(f"Invalid feature type: {type(feature)}")
                raise ValueError(f"Feature must be a string, got {type(feature)}")
            
            if ":" not in feature:
                logger.error(f"Invalid feature format: {feature}")
                raise ValueError(f"Feature must be in format 'category:feature' or 'category:*', got: {feature}")
            
            category, feature_name = feature.split(":", 1)
            
            # Handle wildcard pattern
            if feature_name == "*":
                if category not in mapping:
                    mapping[category] = []
                mapping[category] = ["*"]  # Override with wildcard
                logger.debug(f"Added wildcard pattern for category: {category}")
            else:
                if category not in mapping:
                    mapping[category] = []
                # Only add if not already wildcard
                if "*" not in mapping[category]:
                    mapping[category].append(feature_name)
                else:
                    logger.debug(f"Skipping {feature_name} for {category} - already has wildcard")
        
        logger.debug(f"Converted feature list to mapping: {len(mapping)} categories")
        return mapping
    
    @staticmethod
    def convert_feature_list_to_items(feature_list: List[Dict]) -> Dict[str, Dict]:
        """
        Convert feature list to items format for write operations.
        
        Args:
            feature_list: List of feature objects with category and features
            
        Returns:
            Items in format {"cat1": {"f1": "v1", "f2": "v2"}}
        """
        if not feature_list:
            logger.error("Empty feature list provided")
            raise ValueError("Feature list cannot be empty")
        
        if not isinstance(feature_list, list):
            logger.error(f"Invalid feature list type: {type(feature_list)}")
            raise ValueError("Feature list must be a list")
        
        items = {}
        for item in feature_list:
            if not isinstance(item, dict):
                logger.error(f"Invalid feature item type: {type(item)}")
                raise ValueError(f"Feature item must be a dictionary, got {type(item)}")
            
            if "category" not in item:
                logger.error("Missing category in feature item")
                raise ValueError("Feature item must contain 'category' field")
            
            if "features" not in item:
                logger.error("Missing features in feature item")
                raise ValueError("Feature item must contain 'features' field")
            
            category = item["category"]
            features = item["features"]
            
            if not isinstance(category, str):
                logger.error(f"Invalid category type: {type(category)}")
                raise ValueError(f"Category must be a string, got {type(category)}")
            
            if not isinstance(features, dict):
                logger.error(f"Invalid features type: {type(features)}")
                raise ValueError(f"Features must be a dictionary, got {type(features)}")
            
            items[category] = features
        
        logger.debug(f"Converted feature list to items: {len(items)} categories")
        return items
