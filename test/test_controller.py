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
        mock_services.convert_feature_list_to_mapping.return_value = {
            'd0_unauth_features': ['credit_score']
        }
        # Mock validate_mapping to return valid mapping and no invalid categories
        mock_services.validate_mapping.return_value = (
            {'d0_unauth_features': ['credit_score']},  # valid_mapping
            []  # invalid_categories
        )
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
        assert result['unavailable_feature_categories'] == []
        mock_flows.get_multiple_categories_flow.assert_called_once()
    
    def test_get_multiple_categories_invalid_structure(self):
        """Test with invalid request structure - should raise KeyError"""
        request_data = {'invalid': 'data'}  # Missing 'data' key
        
        with pytest.raises(KeyError):
            FeatureController.get_multiple_categories(request_data)


class TestUpsertCategoryController:
    """Tests for upsert_category controller (single category writes)"""
    
    @patch('components.features.controller.FeatureFlows')
    @patch('components.features.controller.FeatureServices')
    def test_upsert_category_success(self, mock_services, mock_flows):
        """Test upserting single category successfully"""
        mock_services.validate_single_category_write.return_value = None
        mock_flows.upsert_category_flow.return_value = {
            'message': 'Category written successfully (full replace)',
            'entity_value': 'test-123',
            'entity_type': 'bright_uid',
            'category': 'd0_unauth_features',
            'feature_count': 1
        }
        
        request_data = {
            'meta': {'source': 'prediction_service'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'category': 'd0_unauth_features',
                'features': {'credit_score': 750}
            }
        }
        
        result = FeatureController.upsert_category(request_data)
        
        assert result['message'] == 'Category written successfully (full replace)'
        assert result['category'] == 'd0_unauth_features'
        assert result['feature_count'] == 1
        mock_services.validate_single_category_write.assert_called_once_with('d0_unauth_features', {'credit_score': 750})
        mock_flows.upsert_category_flow.assert_called_once_with('test-123', 'd0_unauth_features', {'credit_score': 750}, 'bright_uid')
    
    @patch('components.features.controller.FeatureServices')
    def test_upsert_category_invalid_category(self, mock_services):
        """Test upserting with invalid category"""
        mock_services.validate_single_category_write.side_effect = ValueError('Category not allowed')
        
        request_data = {
            'meta': {'source': 'prediction_service'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'category': 'invalid_category',
                'features': {'feature': 'value'}
            }
        }
        
        with pytest.raises(ValueError):
            FeatureController.upsert_category(request_data)


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


