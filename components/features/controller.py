"""
Controller layer for feature operations.
Orchestrates flows and services for clean API endpoints.
"""
from typing import Dict, List
from components.features.flows import FeatureFlows
from components.features.services import FeatureServices
from core.logging_config import get_logger

# Configure logger
logger = get_logger("feature_controller")

class FeatureController:
    """Controller for feature operations."""
    
    @staticmethod
    def get_single_category(entity_value: str, category: str, entity_type: str) -> Dict:
        """
        Controller for getting a single category's features.
        
        Args:
            entity_value: User/account identifier
            category: Feature category
            entity_type: Entity type (bright_uid or account_id)
            
        Returns:
            Dict containing the item data
        """
        logger.info(f"Controller: Getting single category {entity_value}/{category}")
        
        # Validate category is in whitelist (path parameter, not validated by Pydantic)
        FeatureServices.validate_category_for_read(category)
        
        # Execute flow
        return FeatureFlows.get_single_category_flow(entity_value, category, entity_type)
    
    @staticmethod
    def get_multiple_categories(request_data: Dict) -> Dict:
        """
        Controller for getting multiple categories with filtering.
        
        Args:
            request_data: Request containing meta and data with identifier and feature_list
            
        Returns:
            Dict containing results and missing categories
        """
        logger.info("Controller: Getting multiple categories from request data")
        
        # Extract data (Pydantic already validated structure)
        data = request_data["data"]
        entity_type = data["entity_type"]
        entity_value = data["entity_value"]
        feature_list = data["feature_list"]
        
        # Convert feature_list to mapping format
        mapping = FeatureServices.convert_feature_list_to_mapping(feature_list)
        
        # Validate categories are in whitelist (business rule)
        # Returns valid categories and list of invalid ones for graceful handling
        valid_mapping, invalid_categories = FeatureServices.validate_mapping(mapping)
        
        # Execute flow with valid categories only (no DB calls for invalid categories)
        result = FeatureFlows.get_multiple_categories_flow(entity_value, valid_mapping, entity_type)
        
        # Add invalid categories to unavailable list (no DB calls made for these)
        result['unavailable_feature_categories'].extend(invalid_categories)
        
        return result
    
    @staticmethod
    def upsert_features(request_data: Dict) -> Dict:
        """
        Controller for upserting features.
        
        Args:
            request_data: Request containing meta and data with identifier and feature_list
            
        Returns:
            Dict containing operation results
        """
        logger.info("Controller: Upserting features from request data")
        
        # Extract data (Pydantic already validated structure)
        data = request_data["data"]
        entity_type = data["entity_type"]
        entity_value = data["entity_value"]
        feature_list = data["feature_list"]
        
        # Convert feature_list to items format
        items = FeatureServices.convert_feature_list_to_items(feature_list)
        
        # Validate items (business rules: category whitelist)
        FeatureServices.validate_items(items)
        
        # Execute flow
        return FeatureFlows.upsert_features_flow(entity_value, items, entity_type)
