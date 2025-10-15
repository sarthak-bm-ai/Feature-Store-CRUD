"""
Service layer for feature operations.
Handles validation, business rules, and data transformation.
"""
from typing import Dict, List, Optional, Any
from core.logging_config import get_logger
from core.settings import settings

# Configure logger
logger = get_logger("feature_services")

class FeatureServices:
    """Service layer for feature operations."""
    
    
    
    @staticmethod
    def validate_category_for_write(category: str) -> None:
        """
        Validate that category is allowed for write operations.
        
        Args:
            category: Category name to validate
            
        Raises:
            ValueError: If category is not in allowed list
        """
        allowed_categories = settings.ALLOWED_WRITE_CATEGORIES
        
        if category not in allowed_categories:
            logger.error(f"Category '{category}' not in allowed write categories: {allowed_categories}")
            raise ValueError(
                f"Category '{category}' is not allowed for write operations. "
                f"Allowed categories: {', '.join(allowed_categories)}"
            )
        
        logger.debug(f"Category validated for write: {category}")
    
    @staticmethod
    def validate_items(items: Dict[str, Dict]) -> None:
        """
        Validate items for upsert operations.
        Only validates business rules (category whitelist).
        Type checking is handled by Pydantic models.
        
        Args:
            items: Items to validate
            
        Raises:
            ValueError: If category is not in allowed list
        """
        # Only validate business rule: category must be in whitelist
        for category in items.keys():
            FeatureServices.validate_category_for_write(category)
        
        logger.debug(f"Items validated: {len(items)} categories")
    
    
    @staticmethod
    def validate_category_for_read(category: str) -> None:
        """
        Validate that category is allowed for read operations.
        
        Args:
            category: Category name to validate
            
        Raises:
            ValueError: If category is not in allowed list
        """
        allowed_categories = settings.ALLOWED_READ_CATEGORIES
        
        if category not in allowed_categories:
            logger.error(f"Category '{category}' not in allowed read categories: {allowed_categories}")
            raise ValueError(
                f"Category '{category}' is not allowed for read operations. "
                f"Allowed categories: {', '.join(allowed_categories)}"
            )
        
        logger.debug(f"Category validated for read: {category}")
    
    @staticmethod
    def validate_mapping(mapping: Dict[str, List[str]]) -> tuple[Dict[str, List[str]], List[str]]:
        """
        Validate categories in mapping and separate valid from invalid ones.
        For graceful handling: returns valid categories and list of invalid categories.
        
        Args:
            mapping: Feature mapping to validate
            
        Returns:
            Tuple of (valid_mapping, invalid_categories)
        """
        allowed_categories = settings.ALLOWED_READ_CATEGORIES
        valid_mapping = {}
        invalid_categories = []
        
        for category, features in mapping.items():
            if category in allowed_categories:
                valid_mapping[category] = features
                logger.debug(f"Category validated for read: {category}")
            else:
                invalid_categories.append(category)
                logger.warning(f"Category '{category}' not in allowed read categories, skipping")
        
        logger.debug(f"Mapping validated: {len(valid_mapping)} valid, {len(invalid_categories)} invalid categories")
        return valid_mapping, invalid_categories
    
    
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
    def validate_single_category_write(category: str, features: Dict[str, Any]) -> None:
        """
        Validate single category write operation.
        
        Args:
            category: Category name
            features: Features dictionary
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(category, str):
            logger.error(f"Invalid category type: {type(category)}")
            raise ValueError(f"Category must be a string, got {type(category)}")
        
        if not isinstance(features, dict):
            logger.error(f"Invalid features type: {type(features)}")
            raise ValueError(f"Features must be a dictionary, got {type(features)}")
        
        if len(features) == 0:
            logger.error("Empty features dictionary")
            raise ValueError("Features dictionary cannot be empty")
        
        # Validate category is in whitelist
        FeatureServices.validate_category_for_write(category)
        
        logger.debug(f"Validated single category write: {category} with {len(features)} features")
