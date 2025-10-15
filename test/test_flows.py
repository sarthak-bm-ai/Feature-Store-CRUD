"""
Unit tests for flows layer
"""
import pytest
from unittest.mock import MagicMock, patch, Mock

from components.features.flows import FeatureFlows


class TestGetMultipleCategoriesFlow:
    """Tests for get_multiple_categories_flow"""
    
    @patch('components.features.flows.crud')
    def test_get_single_category_with_features(self, mock_crud):
        """Test getting single category with specific features"""
        mock_crud.get_item.return_value = {
            'bright_uid': 'test-123',
            'category': 'd0_unauth_features',
            'features': {
                'data': {
                    'credit_score': 750,
                    'age': 30,
                    'income': 60000
                },
                'meta': {
                    'created_at': '2025-10-14T12:34:56.789Z',
                    'updated_at': '2025-10-14T12:34:56.789Z',
                    'compute_id': None
                }
            }
        }
        
        mapping = {
            'd0_unauth_features': ['credit_score', 'age']
        }
        
        result = FeatureFlows.get_multiple_categories_flow(
            'test-123',
            mapping,
            'bright_uid'
        )
        
        assert result['entity_value'] == 'test-123'
        assert result['entity_type'] == 'bright_uid'
        assert 'd0_unauth_features' in result['items']
        # Should only include requested features
        assert 'credit_score' in result['items']['d0_unauth_features']['features']['data']
        assert 'age' in result['items']['d0_unauth_features']['features']['data']
        # Should not include income (not requested)
        assert 'income' not in result['items']['d0_unauth_features']['features']['data']
        assert result['unavailable_feature_categories'] == []
    
    @patch('components.features.flows.crud')
    def test_get_category_with_wildcard(self, mock_crud):
        """Test getting category with wildcard (all features)"""
        mock_crud.get_item.return_value = {
            'bright_uid': 'test-123',
            'category': 'd0_unauth_features',
            'features': {
                'data': {
                    'credit_score': 750,
                    'age': 30,
                    'income': 60000,
                    'debt_ratio': 0.35
                },
                'meta': {
                    'created_at': '2025-10-14T12:34:56.789Z',
                    'updated_at': '2025-10-14T12:34:56.789Z',
                    'compute_id': None
                }
            }
        }
        
        mapping = {
            'd0_unauth_features': ['*']
        }
        
        result = FeatureFlows.get_multiple_categories_flow(
            'test-123',
            mapping,
            'bright_uid'
        )
        
        assert 'd0_unauth_features' in result['items']
        # Should include all features
        assert len(result['items']['d0_unauth_features']['features']['data']) == 4
        assert 'credit_score' in result['items']['d0_unauth_features']['features']['data']
        assert 'income' in result['items']['d0_unauth_features']['features']['data']
    
    @patch('components.features.flows.crud')
    def test_get_multiple_categories(self, mock_crud):
        """Test getting multiple categories"""
        
        def mock_get_item(entity_value, category, entity_type):
            if category == 'd0_unauth_features':
                return {
                    'bright_uid': entity_value,
                    'category': category,
                    'features': {
                        'data': {'credit_score': 750},
                        'meta': {
                            'created_at': '2025-10-14T12:34:56.789Z',
                            'updated_at': '2025-10-14T12:34:56.789Z',
                            'compute_id': None
                        }
                    }
                }
            elif category == 'ncr_unauth_features':
                return {
                    'bright_uid': entity_value,
                    'category': category,
                    'features': {
                        'data': {'transactions': 10},
                        'meta': {
                            'created_at': '2025-10-14T12:34:56.789Z',
                            'updated_at': '2025-10-14T12:34:56.789Z',
                            'compute_id': None
                        }
                    }
                }
            return None
        
        mock_crud.get_item.side_effect = mock_get_item
        
        mapping = {
            'd0_unauth_features': ['credit_score'],
            'ncr_unauth_features': ['transactions']
        }
        
        result = FeatureFlows.get_multiple_categories_flow(
            'test-123',
            mapping,
            'bright_uid'
        )
        
        assert len(result['items']) == 2
        assert 'd0_unauth_features' in result['items']
        assert 'ncr_unauth_features' in result['items']
    
    @patch('components.features.flows.crud')
    def test_get_missing_category(self, mock_crud):
        """Test getting non-existent category raises ValueError"""
        mock_crud.get_item.return_value = None
        
        mapping = {
            'd0_unauth_features': ['credit_score']
        }
        
        # Should raise ValueError when no items found
        with pytest.raises(ValueError) as exc_info:
            FeatureFlows.get_multiple_categories_flow(
                'test-123',
                mapping,
                'bright_uid'
            )
        
        assert "No items found" in str(exc_info.value)
    
    @patch('components.features.flows.crud')
    def test_get_partial_missing_categories(self, mock_crud):
        """Test getting with some categories missing"""
        
        def mock_get_item(entity_value, category, entity_type):
            if category == 'd0_unauth_features':
                return {
                    'bright_uid': entity_value,
                    'category': category,
                    'features': {
                        'data': {'credit_score': 750},
                        'meta': {
                            'created_at': '2025-10-14T12:34:56.789Z',
                            'updated_at': '2025-10-14T12:34:56.789Z',
                            'compute_id': None
                        }
                    }
                }
            return None
        
        mock_crud.get_item.side_effect = mock_get_item
        
        mapping = {
            'd0_unauth_features': ['credit_score'],
            'missing_category': ['feature']
        }
        
        result = FeatureFlows.get_multiple_categories_flow(
            'test-123',
            mapping,
            'bright_uid'
        )
        
        assert len(result['items']) == 1
        assert 'd0_unauth_features' in result['items']
        assert 'missing_category' in result['unavailable_feature_categories']


class TestUpsertFeaturesFlow:
    """Tests for upsert_features_flow"""
    
    @patch('components.features.flows.publish_feature_availability_event')
    @patch('components.features.flows.crud')
    def test_upsert_single_category(self, mock_crud, mock_publish):
        """Test upserting single category"""
        mock_publish.return_value = True
        
        items = {
            'd0_unauth_features': {
                'credit_score': 750,
                'age': 30
            }
        }
        
        result = FeatureFlows.upsert_features_flow(
            'test-123',
            items,
            'bright_uid'
        )
        
        assert 'message' in result
        assert result['entity_value'] == 'test-123'
        assert result['entity_type'] == 'bright_uid'
        assert 'd0_unauth_features' in result['results']
        assert result['results']['d0_unauth_features']['status'] == 'replaced'
        mock_crud.upsert_item_with_meta.assert_called_once()
        mock_publish.assert_called_once()
    
    @patch('components.features.flows.publish_feature_availability_event')
    @patch('components.features.flows.crud')
    def test_upsert_multiple_categories(self, mock_crud, mock_publish):
        """Test upserting multiple categories"""
        mock_publish.return_value = True
        
        items = {
            'd0_unauth_features': {'credit_score': 750},
            'ncr_unauth_features': {'transactions': 10}
        }
        
        result = FeatureFlows.upsert_features_flow(
            'test-123',
            items,
            'bright_uid'
        )
        
        assert len(result['results']) == 2
        assert 'd0_unauth_features' in result['results']
        assert 'ncr_unauth_features' in result['results']
        assert mock_crud.upsert_item_with_meta.call_count == 2
        assert mock_publish.call_count == 2
    
    @patch('components.features.flows.publish_feature_availability_event')
    @patch('components.features.flows.crud')
    def test_upsert_with_kafka_failure(self, mock_crud, mock_publish):
        """Test upserting when Kafka publishing fails"""
        mock_publish.return_value = False  # Kafka failed
        
        items = {
            'd0_unauth_features': {'credit_score': 750}
        }
        
        # Should still succeed even if Kafka fails
        result = FeatureFlows.upsert_features_flow(
            'test-123',
            items,
            'bright_uid'
        )
        
        assert 'message' in result
        assert 'd0_unauth_features' in result['results']
    
    @patch('components.features.flows.publish_feature_availability_event')
    @patch('components.features.flows.crud')
    def test_upsert_with_kafka_exception(self, mock_crud, mock_publish):
        """Test upserting when Kafka raises exception"""
        mock_publish.side_effect = Exception('Kafka connection failed')
        
        items = {
            'd0_unauth_features': {'credit_score': 750}
        }
        
        # Should still succeed even if Kafka throws exception
        result = FeatureFlows.upsert_features_flow(
            'test-123',
            items,
            'bright_uid'
        )
        
        assert 'message' in result


class TestFilterFeatures:
    """Tests for _filter_features"""
    
    def test_filter_specific_features(self):
        """Test filtering to specific features"""
        item = {
            'bright_uid': 'test-123',
            'category': 'd0_unauth_features',
            'features': {
                'data': {
                    'credit_score': 750,
                    'age': 30,
                    'income': 60000
                },
                'meta': {
                    'created_at': '2025-10-14T12:34:56.789Z',
                    'updated_at': '2025-10-14T12:34:56.789Z'
                }
            }
        }
        
        features_to_keep = {'credit_score', 'age'}
        result = FeatureFlows._filter_features(item, features_to_keep)
        
        assert 'credit_score' in result['features']['data']
        assert 'age' in result['features']['data']
        assert 'income' not in result['features']['data']
        assert 'meta' in result['features']
    
    def test_filter_with_missing_features(self):
        """Test filtering when some requested features don't exist"""
        item = {
            'bright_uid': 'test-123',
            'category': 'd0_unauth_features',
            'features': {
                'data': {
                    'credit_score': 750
                },
                'meta': {
                    'created_at': '2025-10-14T12:34:56.789Z',
                    'updated_at': '2025-10-14T12:34:56.789Z'
                }
            }
        }
        
        features_to_keep = {'credit_score', 'non_existent'}
        result = FeatureFlows._filter_features(item, features_to_keep)
        
        assert 'credit_score' in result['features']['data']
        assert 'non_existent' not in result['features']['data']
    
    def test_filter_empty_set(self):
        """Test filtering with empty feature set returns item unchanged"""
        item = {
            'bright_uid': 'test-123',
            'category': 'd0_unauth_features',
            'features': {
                'data': {
                    'credit_score': 750,
                    'age': 30
                },
                'meta': {
                    'created_at': '2025-10-14T12:34:56.789Z',
                    'updated_at': '2025-10-14T12:34:56.789Z'
                }
            }
        }
        
        result = FeatureFlows._filter_features(item, set())
        
        # Empty set means no filtering - return item unchanged
        assert result['features']['data'] == item['features']['data']
        assert 'meta' in result['features']


