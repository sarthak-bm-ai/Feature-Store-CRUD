"""
Unit tests for controller layer
"""
import pytest
from unittest.mock import MagicMock, patch

from components.features.controller import FeatureController


class TestGetMultipleCategoriesController:
    """Tests for get_multiple_categories controller"""
    
    @patch('components.features.controller.FeatureFlows')
    @patch('components.features.controller.FeatureServices')
    def test_get_multiple_categories_success(self, mock_services, mock_flows):
        """Test getting multiple categories successfully"""
        mock_services.validate_request_structure.return_value = (
            {'source': 'api'},
            {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'feature_list': ['d0_unauth_features:credit_score']
            }
        )
        mock_services.sanitize_entity_value.return_value = 'test-123'
        mock_services.convert_feature_list_to_mapping.return_value = {
            'd0_unauth_features': ['credit_score']
        }
        mock_flows.get_multiple_categories_flow.return_value = {
            'entity_value': 'test-123',
            'entity_type': 'bright_uid',
            'items': {
                'd0_unauth_features': {
                    'data': {'credit_score': 750},
                    'meta': {
                        'created_at': '2025-10-14T12:34:56.789Z',
                        'updated_at': '2025-10-14T12:34:56.789Z'
                    }
                }
            },
            'unavailable_feature_categories': []
        }
        
        request_data = {
            'meta': {'source': 'api'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'feature_list': ['d0_unauth_features:credit_score']
            }
        }
        
        result = FeatureController.get_multiple_categories(request_data)
        
        assert result['entity_value'] == 'test-123'
        assert 'd0_unauth_features' in result['items']
        mock_services.validate_request_structure.assert_called_once_with(request_data)
        mock_flows.get_multiple_categories_flow.assert_called_once()
    
    @patch('components.features.controller.FeatureServices')
    def test_get_multiple_categories_invalid_structure(self, mock_services):
        """Test with invalid request structure"""
        mock_services.validate_request_structure.side_effect = ValueError('Invalid request structure')
        
        request_data = {'invalid': 'data'}
        
        with pytest.raises(ValueError):
            FeatureController.get_multiple_categories(request_data)


class TestUpsertFeaturesController:
    """Tests for upsert_features controller"""
    
    @patch('components.features.controller.FeatureFlows')
    @patch('components.features.controller.FeatureServices')
    def test_upsert_features_success(self, mock_services, mock_flows):
        """Test upserting features successfully"""
        mock_services.validate_request_structure.return_value = (
            {'source': 'prediction_service'},
            {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'feature_list': [
                    {
                        'category': 'd0_unauth_features',
                        'features': {'credit_score': 750}
                    }
                ]
            }
        )
        mock_services.validate_source.return_value = None
        mock_services.sanitize_entity_value.return_value = 'test-123'
        mock_services.validate_items.return_value = None
        mock_services.convert_feature_list_to_items.return_value = {
            'd0_unauth_features': {'credit_score': 750}
        }
        mock_flows.upsert_features_flow.return_value = {
            'message': 'Features upserted successfully',
            'entity_value': 'test-123',
            'entity_type': 'bright_uid',
            'categories_updated': ['d0_unauth_features'],
            'timestamp': '2025-10-14T12:34:56.789Z'
        }
        
        request_data = {
            'meta': {'source': 'prediction_service'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'feature_list': [
                    {
                        'category': 'd0_unauth_features',
                        'features': {'credit_score': 750}
                    }
                ]
            }
        }
        
        result = FeatureController.upsert_features(request_data)
        
        assert result['message'] == 'Features upserted successfully'
        assert 'd0_unauth_features' in result['categories_updated']
        # Note: validate_source is done at Pydantic model level, not in controller
        mock_services.validate_items.assert_called_once()
        mock_flows.upsert_features_flow.assert_called_once()
    
    @patch('components.features.controller.FeatureServices')
    def test_upsert_features_invalid_category(self, mock_services):
        """Test upserting with invalid category"""
        mock_services.validate_request_structure.return_value = (
            {'source': 'prediction_service'},
            {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'feature_list': []
            }
        )
        mock_services.convert_feature_list_to_items.return_value = {
            'invalid_category': {'feature': 'value'}
        }
        mock_services.validate_table_type.return_value = None
        mock_services.sanitize_entity_value.return_value = 'test-123'
        mock_services.validate_items.side_effect = ValueError('Category not allowed')
        
        request_data = {
            'meta': {'source': 'prediction_service'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'feature_list': []
            }
        }
        
        with pytest.raises(ValueError):
            FeatureController.upsert_features(request_data)


class TestGetSingleCategoryController:
    """Tests for get_single_category controller"""
    
    @patch('components.features.controller.FeatureFlows')
    @patch('components.features.controller.FeatureServices')
    def test_get_single_category_success(self, mock_services, mock_flows):
        """Test getting single category successfully"""
        mock_services.validate_table_type.return_value = None
        mock_services.sanitize_entity_value.return_value = 'test-123'
        mock_services.sanitize_category.return_value = 'd0_unauth_features'
        mock_flows.get_single_category_flow.return_value = {
            'entity_value': 'test-123',
            'entity_type': 'bright_uid',
            'category': 'd0_unauth_features',
            'features': {
                'data': {'credit_score': 750},
                'meta': {
                    'created_at': '2025-10-14T12:34:56.789Z',
                    'updated_at': '2025-10-14T12:34:56.789Z'
                }
            }
        }
        
        result = FeatureController.get_single_category(
            'test-123',
            'd0_unauth_features',
            'bright_uid'
        )
        
        assert result['entity_value'] == 'test-123'
        assert result['entity_type'] == 'bright_uid'
        assert result['category'] == 'd0_unauth_features'
        assert 'features' in result
        mock_flows.get_single_category_flow.assert_called_once_with('test-123', 'd0_unauth_features', 'bright_uid')
    
    @patch('components.features.controller.FeatureFlows')
    @patch('components.features.controller.FeatureServices')
    def test_get_single_category_not_found(self, mock_services, mock_flows):
        """Test getting non-existent category"""
        mock_services.validate_table_type.return_value = None
        mock_services.sanitize_entity_value.return_value = 'test-123'
        mock_services.sanitize_category.return_value = 'd0_unauth_features'
        mock_flows.get_single_category_flow.side_effect = ValueError('Category not found')
        
        with pytest.raises(ValueError) as exc_info:
            FeatureController.get_single_category(
                'test-123',
                'd0_unauth_features',
                'bright_uid'
            )
        
        assert 'not found' in str(exc_info.value).lower()


