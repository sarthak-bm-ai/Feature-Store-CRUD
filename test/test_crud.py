"""
Unit tests for CRUD operations
"""
import pytest
from unittest.mock import MagicMock, patch, Mock
from decimal import Decimal
from datetime import datetime
from botocore.exceptions import ClientError

from components.features import crud


class TestGetItem:
    """Tests for get_item"""
    
    @patch('components.features.crud.get_table')
    def test_get_item_success(self, mock_get_table):
        """Test getting item successfully"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'bright_uid': 'test-123',
                'category': 'd0_unauth_features',
                'features': {
                    'data': {'credit_score': Decimal('750')},
                    'meta': {
                        'created_at': '2025-10-14T12:34:56.789Z',
                        'updated_at': '2025-10-14T12:34:56.789Z',
                        'compute_id': None
                    }
                }
            }
        }
        mock_get_table.return_value = mock_table
        
        result = crud.get_item('test-123', 'd0_unauth_features', 'bright_uid')
        
        assert result is not None
        assert result['bright_uid'] == 'test-123'
        assert result['category'] == 'd0_unauth_features'
        assert 'features' in result
        assert result['features']['data']['credit_score'] == 750.0
        mock_table.get_item.assert_called_once()
    
    @patch('components.features.crud.get_table')
    def test_get_item_not_found(self, mock_get_table):
        """Test getting non-existent item"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_get_table.return_value = mock_table
        
        result = crud.get_item('test-123', 'd0_unauth_features', 'bright_uid')
        
        assert result is None
    
    @patch('components.features.crud.get_table')
    def test_get_item_client_error(self, mock_get_table):
        """Test getting item with client error"""
        mock_table = MagicMock()
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
            'GetItem'
        )
        mock_get_table.return_value = mock_table
        
        with pytest.raises(ClientError):
            crud.get_item('test-123', 'd0_unauth_features', 'bright_uid')
    
    @patch('components.features.crud.get_table')
    def test_get_item_account_uid(self, mock_get_table):
        """Test getting item with account_uid"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'account_uid': 'account-123',
                'category': 'd0_unauth_features',
                'features': {
                    'data': {'age': Decimal('30')},
                    'meta': {
                        'created_at': '2025-10-14T12:34:56.789Z',
                        'updated_at': '2025-10-14T12:34:56.789Z',
                        'compute_id': None
                    }
                }
            }
        }
        mock_get_table.return_value = mock_table
        
        result = crud.get_item('account-123', 'd0_unauth_features', 'account_uid')
        
        assert result is not None
        assert result['account_uid'] == 'account-123'
        assert result['features']['data']['age'] == 30.0


class TestUpsertItemWithMeta:
    """Tests for upsert_item_with_meta"""
    
    @patch('components.features.crud.get_current_timestamp')
    @patch('components.features.crud.get_table')
    def test_upsert_new_item(self, mock_get_table, mock_timestamp):
        """Test upserting new item"""
        mock_timestamp.return_value = '2025-10-14T12:34:56.789Z'
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_get_table.return_value = mock_table
        
        crud.upsert_item_with_meta(
            'test-123',
            'd0_unauth_features',
            {'credit_score': 750},
            'bright_uid'
        )
        
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']
        assert call_args['bright_uid'] == 'test-123'
        assert call_args['category'] == 'd0_unauth_features'
        assert 'features' in call_args
    
    @patch('components.features.crud.get_current_timestamp')
    @patch('components.features.crud.get_table')
    def test_upsert_existing_item(self, mock_get_table, mock_timestamp):
        """Test upserting existing item (updates features)"""
        mock_timestamp.return_value = '2025-10-14T12:34:56.789Z'
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'buid': 'test-123',
                'category': 'd0_unauth_features',
                'features': {
                    'data': {'old_feature': 100},
                    'meta': {
                        'created_at': '2025-10-10T12:34:56.789Z',
                        'updated_at': '2025-10-10T12:34:56.789Z',
                        'compute_id': None
                    }
                }
            }
        }
        mock_get_table.return_value = mock_table
        
        crud.upsert_item_with_meta(
            'test-123',
            'd0_unauth_features',
            {'credit_score': 750, 'new_feature': 200},
            'bright_uid'
        )
        
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']
        # Should preserve created_at but update updated_at
        assert 'features' in call_args
    
    @patch('components.features.crud.get_current_timestamp')
    @patch('components.features.crud.get_table')
    def test_upsert_with_float_conversion(self, mock_get_table, mock_timestamp):
        """Test upserting with float to Decimal conversion"""
        mock_timestamp.return_value = '2025-10-14T12:34:56.789Z'
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_get_table.return_value = mock_table
        
        crud.upsert_item_with_meta(
            'test-123',
            'd0_unauth_features',
            {'credit_score': 750.5, 'ratio': 0.35},
            'bright_uid'
        )
        
        mock_table.put_item.assert_called_once()
        # Verify the conversion happened without errors


class TestConvertFloatsToDecimal:
    """Tests for _convert_floats_to_decimal"""
    
    def test_convert_simple_float(self):
        """Test converting simple float"""
        from components.features.crud import _convert_floats_to_decimal
        result = _convert_floats_to_decimal(123.45)
        assert isinstance(result, Decimal)
        assert result == Decimal('123.45')
    
    def test_convert_dict_with_floats(self):
        """Test converting dict with floats"""
        from components.features.crud import _convert_floats_to_decimal
        data = {'credit_score': 750.5, 'ratio': 0.35, 'name': 'test'}
        result = _convert_floats_to_decimal(data)
        assert isinstance(result['credit_score'], Decimal)
        assert isinstance(result['ratio'], Decimal)
        assert isinstance(result['name'], str)
    
    def test_convert_nested_dict(self):
        """Test converting nested dict"""
        from components.features.crud import _convert_floats_to_decimal
        data = {
            'features': {
                'credit_score': 750.5,
                'nested': {
                    'ratio': 0.35
                }
            }
        }
        result = _convert_floats_to_decimal(data)
        assert isinstance(result['features']['credit_score'], Decimal)
        assert isinstance(result['features']['nested']['ratio'], Decimal)
    
    def test_convert_list_with_floats(self):
        """Test converting list with floats"""
        from components.features.crud import _convert_floats_to_decimal
        data = [123.45, 678.90, 'string', 100]
        result = _convert_floats_to_decimal(data)
        assert isinstance(result[0], Decimal)
        assert isinstance(result[1], Decimal)
        assert result[2] == 'string'
        assert result[3] == 100
    
    def test_convert_datetime(self):
        """Test converting datetime"""
        from components.features.crud import _convert_floats_to_decimal
        dt = datetime(2025, 10, 14, 12, 34, 56, 789000)
        result = _convert_floats_to_decimal(dt)
        assert isinstance(result, str)
        assert '2025-10-14' in result


class TestDynamoDBToDict:
    """Tests for dynamodb_to_dict"""
    
    def test_deserialize_dict_with_typed_values(self):
        """Test deserializing dict with DynamoDB-typed values"""
        from components.features.crud import dynamodb_to_dict
        dynamo_item = {
            'name': {'S': 'string_value'},
            'age': {'N': '30'}
        }
        result = dynamodb_to_dict(dynamo_item)
        assert result['name'] == 'string_value'
        assert result['age'] == 30
    
    def test_deserialize_nested_map(self):
        """Test deserializing nested map"""
        from components.features.crud import dynamodb_to_dict
        dynamo_item = {
            'data': {
                'credit_score': Decimal('750'),
                'name': 'test'
            }
        }
        result = dynamodb_to_dict(dynamo_item)
        assert isinstance(result, dict)
        assert result['data']['credit_score'] == 750.0
        assert result['data']['name'] == 'test'
    
    def test_deserialize_decimal_conversion(self):
        """Test that Decimals are converted to float"""
        from components.features.crud import dynamodb_to_dict
        dynamo_item = {
            'score': Decimal('750.5')
        }
        result = dynamodb_to_dict(dynamo_item)
        assert isinstance(result['score'], float)
        assert result['score'] == 750.5


class TestDictToDynamoDB:
    """Tests for dict_to_dynamodb"""
    
    def test_serialize_simple_types(self):
        """Test serializing simple types"""
        from components.features.crud import dict_to_dynamodb
        python_dict = {
            'name': 'test',
            'age': 30,
            'score': 750.5
        }
        result = dict_to_dynamodb(python_dict)
        assert 'M' in result
        assert 'name' in result['M']
    
    def test_serialize_nested_dict(self):
        """Test serializing nested dict"""
        from components.features.crud import dict_to_dynamodb
        python_dict = {
            'data': {
                'credit_score': 750,
                'nested': {
                    'ratio': 0.35
                }
            }
        }
        result = dict_to_dynamodb(python_dict)
        assert 'M' in result
