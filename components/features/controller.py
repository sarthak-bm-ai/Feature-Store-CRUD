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
            entity_type: Entity type (bright_uid or account_pid)
            
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
    def upsert_category(request_data: Dict) -> Dict:
        """
        Controller for upserting a single category's features.
        
        Args:
            request_data: Request containing meta and data with entity info, category, and features
            
        Returns:
            Dict containing operation results
        """
        logger.info("Controller: Upserting single category from request data")
        
        # Extract metadata (compute_id)
        meta = request_data.get("meta", {})
        compute_id = meta.get("compute_id")
        
        # Extract data (Pydantic already validated structure)
        data = request_data["data"]
        entity_type = data["entity_type"]
        entity_value = data["entity_value"]
        category = data["category"]
        features = data["features"]
        
        # Validate single category write (business rules: category whitelist, non-empty features)
        FeatureServices.validate_single_category_write(category, features)
        
        # Execute flow with compute_id
        return FeatureFlows.upsert_category_flow(entity_value, category, features, entity_type, compute_id)
