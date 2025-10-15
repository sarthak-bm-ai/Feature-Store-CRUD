"""
Unit tests for API routes
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint"""
    
    @patch('api.v1.routes.get_all_tables')
    @patch('api.v1.routes.health_check')
    def test_health_check_healthy(self, mock_health_check, mock_get_tables):
        """Test health check when service is healthy"""
        mock_health_check.return_value = True
        mock_get_tables.return_value = {
            'feature_store_bright_uid': 'table_obj',
            'feature_store_account_uid': 'table_obj'
        }
        
        response = client.get('/api/v1/health')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['dynamodb_connection'] is True
        assert len(data['tables_available']) > 0
    
    @patch('api.v1.routes.get_all_tables')
    @patch('api.v1.routes.health_check')
    def test_health_check_unhealthy(self, mock_health_check, mock_get_tables):
        """Test health check when service is unhealthy"""
        mock_health_check.return_value = False
        mock_get_tables.return_value = {}
        
        response = client.get('/api/v1/health')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'unhealthy'
        assert data['dynamodb_connection'] is False


class TestGetItemsEndpoint:
    """Tests for POST /get/items endpoint"""
    
    @patch('api.v1.routes.FeatureController.get_multiple_categories')
    def test_get_items_success(self, mock_get_multiple):
        """Test getting items successfully"""
        mock_get_multiple.return_value = {
            'entity_value': 'test-123',
            'entity_type': 'bright_uid',
            'items': {
                'd0_unauth_features': {
                    'bright_uid': 'test-123',
                    'category': 'd0_unauth_features',
                    'features': {
                        'data': {'credit_score': 750},
                        'meta': {
                            'created_at': '2025-10-14T12:34:56.789Z',
                            'updated_at': '2025-10-14T12:34:56.789Z',
                            'compute_id': None
                        }
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
        
        response = client.post('/api/v1/get/items', json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['entity_value'] == 'test-123'
        assert 'd0_unauth_features' in data['items']
    
    @patch('api.v1.routes.FeatureController.get_multiple_categories')
    def test_get_items_with_wildcard(self, mock_get_multiple):
        """Test getting items with wildcard"""
        mock_get_multiple.return_value = {
            'entity_value': 'test-123',
            'entity_type': 'bright_uid',
            'items': {
                'd0_unauth_features': {
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
            },
            'unavailable_feature_categories': []
        }
        
        request_data = {
            'meta': {'source': 'api'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'feature_list': ['d0_unauth_features:*']
            }
        }
        
        response = client.post('/api/v1/get/items', json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']['d0_unauth_features']['features']['data']) == 3
    
    @patch('api.v1.routes.FeatureController.get_multiple_categories')
    def test_get_items_not_found(self, mock_get_multiple):
        """Test getting non-existent items"""
        mock_get_multiple.side_effect = ValueError('Entity not found')
        
        request_data = {
            'meta': {'source': 'api'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'non-existent',
                'feature_list': ['d0_unauth_features:credit_score']
            }
        }
        
        response = client.post('/api/v1/get/items', json=request_data)
        
        assert response.status_code == 404
    
    def test_get_items_validation_error(self):
        """Test with invalid request data - Pydantic catches this"""
        request_data = {
            'meta': {'source': 'api'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'feature_list': ['invalid_format']  # Missing colon
            }
        }
        
        response = client.post('/api/v1/get/items', json=request_data)
        
        # Pydantic validation returns 422 for validation errors
        assert response.status_code == 422


class TestUpsertCategoryEndpoint:
    """Tests for POST /items endpoint (single category writes)"""
    
    @patch('api.v1.routes.FeatureController.upsert_category')
    def test_upsert_category_success(self, mock_upsert):
        """Test upserting single category successfully"""
        mock_upsert.return_value = {
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
        
        response = client.post('/api/v1/items', json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Category written successfully (full replace)'
        assert data['category'] == 'd0_unauth_features'
        assert data['feature_count'] == 1
    
    def test_upsert_category_invalid_source(self):
        """Test upserting with invalid source - Pydantic validation catches this"""
        request_data = {
            'meta': {'source': 'unauthorized'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'category': 'd0_unauth_features',
                'features': {'credit_score': 750}
            }
        }
        
        response = client.post('/api/v1/items', json=request_data)
        
        # Pydantic validation returns 422 for validation errors
        assert response.status_code == 422
    
    @patch('api.v1.routes.FeatureController.upsert_category')
    def test_upsert_category_invalid_category(self, mock_upsert):
        """Test upserting with invalid category"""
        mock_upsert.side_effect = ValueError('Category not allowed')
        
        request_data = {
            'meta': {'source': 'prediction_service'},
            'data': {
                'entity_type': 'bright_uid',
                'entity_value': 'test-123',
                'category': 'invalid_category',
                'features': {'feature': 'value'}
            }
        }
        
        response = client.post('/api/v1/items', json=request_data)
        
        assert response.status_code == 400


class TestGetSingleCategoryEndpoint:
    """Tests for GET /get/item/{entity_value} endpoint"""
    
    @patch('api.v1.routes.FeatureController.get_single_category')
    def test_get_single_category_success(self, mock_get_single):
        """Test getting single category successfully"""
        mock_get_single.return_value = {
            'entity_value': 'test-123',
            'entity_type': 'bright_uid',
            'category': 'd0_unauth_features',
            'features': {
                'data': {'credit_score': 750},
                'meta': {
                    'created_at': '2025-10-14T12:34:56.789Z',
                    'updated_at': '2025-10-14T12:34:56.789Z',
                    'compute_id': None
                }
            }
        }
        
        response = client.get(
            '/api/v1/get/item/test-123/d0_unauth_features',
            params={
                'entity_type': 'bright_uid'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['entity_value'] == 'test-123'
        assert data['category'] == 'd0_unauth_features'
    
    @patch('api.v1.routes.FeatureController.get_single_category')
    def test_get_single_category_not_found(self, mock_get_single):
        """Test getting non-existent category"""
        mock_get_single.side_effect = ValueError('Category not found')
        
        response = client.get(
            '/api/v1/get/item/non-existent/d0_unauth_features',
            params={
                'entity_type': 'bright_uid'
            }
        )
        
        assert response.status_code == 404
    
    @patch('api.v1.routes.FeatureController.get_single_category')
    def test_get_single_category_with_defaults(self, mock_get_single):
        """Test getting single category with default entity_type"""
        mock_get_single.return_value = {
            'entity_value': 'test-123',
            'entity_type': 'bright_uid',
            'category': 'd0_unauth_features',
            'features': {
                'data': {'credit_score': 750},
                'meta': {
                    'created_at': '2025-10-14T12:34:56.789Z',
                    'updated_at': '2025-10-14T12:34:56.789Z',
                    'compute_id': None
                }
            }
        }
        
        # Call without entity_type param - should use default 'bright_uid'
        response = client.get('/api/v1/get/item/test-123/d0_unauth_features')
        
        assert response.status_code == 200
        mock_get_single.assert_called_once_with('test-123', 'd0_unauth_features', 'bright_uid')


class TestCORSMiddleware:
    """Tests for CORS middleware"""
    
    def test_cors_preflight(self):
        """Test CORS preflight request"""
        response = client.options(
            '/api/v1/health',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST'
            }
        )
        
        assert response.status_code == 200
        assert 'access-control-allow-origin' in response.headers
    
    def test_cors_actual_request(self):
        """Test CORS on actual request"""
        response = client.get(
            '/api/v1/health',
            headers={'Origin': 'http://localhost:3000'}
        )
        
        assert response.status_code == 200
        assert 'access-control-allow-origin' in response.headers


