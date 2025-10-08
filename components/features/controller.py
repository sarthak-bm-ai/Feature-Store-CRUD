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
    def get_single_category(identifier: str, category: str, table_type: str) -> Dict:
        """
        Controller for getting a single category's features.
        
        Args:
            identifier: User/account identifier
            category: Feature category
            table_type: Table type (bright_uid or account_id)
            
        Returns:
            Dict containing the item data
        """
        logger.info(f"Controller: Getting single category {identifier}/{category}")
        
        # Validate inputs
        FeatureServices.validate_table_type(table_type)
        identifier = FeatureServices.sanitize_identifier(identifier)
        category = FeatureServices.sanitize_category(category)
        
        # Execute flow
        return FeatureFlows.get_single_category_flow(identifier, category, table_type)
    
    @staticmethod
    def get_multiple_categories(request_data: Dict) -> Dict:
        """
        Controller for getting multiple categories with filtering.
        
        Args:
            request_data: Request containing metadata and data with identifier and feature_list
            
        Returns:
            Dict containing results and missing categories
        """
        logger.info("Controller: Getting multiple categories from request data")
        
        # Extract and validate request data
        metadata, data = FeatureServices.validate_request_structure(request_data)
        identifier_type = data["identifier"]
        identifier_value = data["identifier_value"]
        feature_list = data["feature_list"]
        
        # Convert feature_list to mapping format
        mapping = FeatureServices.convert_feature_list_to_mapping(feature_list)
        
        # Validate inputs
        FeatureServices.validate_table_type(identifier_type)
        identifier_value = FeatureServices.sanitize_identifier(identifier_value)
        FeatureServices.validate_mapping(mapping)
        
        # Execute flow
        return FeatureFlows.get_multiple_categories_flow(identifier_value, mapping, identifier_type)
    
    @staticmethod
    def upsert_features(request_data: Dict) -> Dict:
        """
        Controller for upserting features.
        
        Args:
            request_data: Request containing metadata and data with identifier and feature_list
            
        Returns:
            Dict containing operation results
        """
        logger.info("Controller: Upserting features from request data")
        
        # Extract and validate request data
        metadata, data = FeatureServices.validate_request_structure(request_data)
        identifier_type = data["identifier"]
        identifier_value = data["identifier_value"]
        feature_list = data["feature_list"]
        
        # Convert feature_list to items format
        items = FeatureServices.convert_feature_list_to_items(feature_list)
        
        # Validate inputs
        FeatureServices.validate_table_type(identifier_type)
        identifier_value = FeatureServices.sanitize_identifier(identifier_value)
        FeatureServices.validate_items(items)
        
        # Execute flow
        return FeatureFlows.upsert_features_flow(identifier_value, items, identifier_type)
