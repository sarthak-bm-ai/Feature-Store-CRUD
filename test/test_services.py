"""
Unit tests for services layer
"""
import pytest
from components.features.services import FeatureServices


class TestValidateRequestStructure:
    """Tests for validate_request_structure"""
    
    def test_valid_request_structure(self):
        """Test validating valid request structure"""
        request_data = {
            "meta": {"source": "api"},
            "data": {
                "entity_type": "bright_uid",
                "entity_value": "test-123",
                "feature_list": ["d0_unauth_features:credit_score"]
            }
        }
        meta, data = FeatureServices.validate_request_structure(request_data)
        assert meta == {"source": "api"}
        assert data["entity_type"] == "bright_uid"
        assert "feature_list" in data
    
    def test_missing_meta(self):
        """Test request missing meta"""
        request_data = {
            "data": {"entity_type": "bright_uid", "entity_value": "test-123"}
        }
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.validate_request_structure(request_data)
        assert "meta" in str(exc_info.value).lower()
    
    def test_missing_data(self):
        """Test request missing data"""
        request_data = {
            "meta": {"source": "api"}
        }
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.validate_request_structure(request_data)
        assert "data" in str(exc_info.value).lower()


class TestSanitizeEntityValue:
    """Tests for sanitize_entity_value"""
    
    def test_sanitize_normal_string(self):
        """Test sanitizing normal string"""
        result = FeatureServices.sanitize_entity_value("test-user-123")
        assert result == "test-user-123"
    
    def test_sanitize_string_with_spaces(self):
        """Test sanitizing string with spaces"""
        result = FeatureServices.sanitize_entity_value("  test user  ")
        assert result == "test user"
    
    def test_sanitize_empty_string(self):
        """Test sanitizing whitespace-only string becomes empty"""
        # Whitespace-only string passes initial check, then becomes empty after strip
        result = FeatureServices.sanitize_entity_value("  ")
        assert result == ""
    
    def test_sanitize_special_characters(self):
        """Test sanitizing with special characters"""
        result = FeatureServices.sanitize_entity_value("test@user#123")
        assert result == "test@user#123"


class TestConvertFeatureListToMapping:
    """Tests for convert_feature_list_to_mapping"""
    
    def test_convert_simple_feature_list(self):
        """Test converting simple feature list"""
        feature_list = [
            "d0_unauth_features:credit_score",
            "d0_unauth_features:age",
            "ncr_unauth_features:transactions"
        ]
        result = FeatureServices.convert_feature_list_to_mapping(feature_list)
        assert "d0_unauth_features" in result
        assert "ncr_unauth_features" in result
        assert "credit_score" in result["d0_unauth_features"]
        assert "age" in result["d0_unauth_features"]
        assert "transactions" in result["ncr_unauth_features"]
    
    def test_convert_with_wildcard(self):
        """Test converting feature list with wildcard"""
        feature_list = ["d0_unauth_features:*"]
        result = FeatureServices.convert_feature_list_to_mapping(feature_list)
        assert "d0_unauth_features" in result
        assert "*" in result["d0_unauth_features"]
    
    def test_convert_mixed_features_and_wildcards(self):
        """Test converting mixed features and wildcards"""
        feature_list = [
            "d0_unauth_features:*",
            "ncr_unauth_features:transactions"
        ]
        result = FeatureServices.convert_feature_list_to_mapping(feature_list)
        assert "*" in result["d0_unauth_features"]
        assert "transactions" in result["ncr_unauth_features"]
    
    def test_convert_invalid_format(self):
        """Test converting invalid format"""
        feature_list = ["invalid_format"]
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.convert_feature_list_to_mapping(feature_list)
        assert "category:feature" in str(exc_info.value)
    
    def test_convert_empty_list(self):
        """Test converting empty list raises error"""
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.convert_feature_list_to_mapping([])
        assert "empty" in str(exc_info.value).lower()


class TestValidateCategoryForWrite:
    """Tests for validate_category_for_write"""
    
    def test_valid_category_d0(self):
        """Test valid category d0_unauth_features"""
        # Should not raise exception
        FeatureServices.validate_category_for_write("d0_unauth_features")
    
    def test_valid_category_ncr(self):
        """Test valid category ncr_unauth_features"""
        # Should not raise exception
        FeatureServices.validate_category_for_write("ncr_unauth_features")
    
    def test_invalid_category(self):
        """Test invalid category"""
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.validate_category_for_write("invalid_category")
        assert "not allowed" in str(exc_info.value)
        assert "d0_unauth_features" in str(exc_info.value)
        assert "ncr_unauth_features" in str(exc_info.value)


class TestValidateItems:
    """Tests for validate_items"""
    
    def test_validate_valid_items(self):
        """Test validating valid items"""
        items = {
            "d0_unauth_features": {"credit_score": 750, "age": 30}
        }
        # Should not raise exception
        FeatureServices.validate_items(items)
    
    def test_validate_multiple_categories(self):
        """Test validating multiple categories"""
        items = {
            "d0_unauth_features": {"credit_score": 750},
            "ncr_unauth_features": {"transactions": 10}
        }
        # Should not raise exception
        FeatureServices.validate_items(items)
    
    def test_validate_invalid_category(self):
        """Test validating with invalid category"""
        items = {
            "invalid_category": {"feature": "value"}
        }
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.validate_items(items)
        assert "not allowed" in str(exc_info.value)
    
    def test_validate_empty_items(self):
        """Test validating with empty items dict"""
        items = {}
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.validate_items(items)
        assert "empty" in str(exc_info.value).lower()
    
    def test_validate_non_dict_features(self):
        """Test validating with non-dict features"""
        items = {
            "d0_unauth_features": "not_a_dict"
        }
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.validate_items(items)
        assert "dictionary" in str(exc_info.value).lower()
    
    def test_validate_non_string_feature_name(self):
        """Test validating with non-string feature name"""
        items = {
            "d0_unauth_features": {123: "value"}
        }
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.validate_items(items)
        assert "string" in str(exc_info.value).lower()



