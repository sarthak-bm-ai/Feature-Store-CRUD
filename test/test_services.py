"""
Unit tests for services layer
"""
import pytest
from components.features.services import FeatureServices


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


class TestValidateCategoryForRead:
    """Tests for validate_category_for_read"""
    
    def test_valid_category_d0(self):
        """Test valid category d0_unauth_features for read"""
        # Should not raise exception
        FeatureServices.validate_category_for_read("d0_unauth_features")
    
    def test_valid_category_ncr(self):
        """Test valid category ncr_unauth_features for read"""
        # Should not raise exception
        FeatureServices.validate_category_for_read("ncr_unauth_features")
    
    def test_invalid_category(self):
        """Test invalid category for read"""
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.validate_category_for_read("invalid_category")
        assert "not allowed" in str(exc_info.value)
        assert "d0_unauth_features" in str(exc_info.value)
        assert "ncr_unauth_features" in str(exc_info.value)


class TestValidateMapping:
    """Tests for validate_mapping - graceful handling of valid and invalid categories"""
    
    def test_valid_mapping(self):
        """Test validating mapping with allowed categories"""
        mapping = {
            "d0_unauth_features": ["credit_score", "age"]
        }
        valid_mapping, invalid_categories = FeatureServices.validate_mapping(mapping)
        assert valid_mapping == mapping
        assert invalid_categories == []
    
    def test_multiple_valid_categories(self):
        """Test validating mapping with multiple allowed categories"""
        mapping = {
            "d0_unauth_features": ["credit_score"],
            "ncr_unauth_features": ["transactions"]
        }
        valid_mapping, invalid_categories = FeatureServices.validate_mapping(mapping)
        assert valid_mapping == mapping
        assert invalid_categories == []
    
    def test_invalid_category_in_mapping(self):
        """Test validating mapping with invalid category - filters it out"""
        mapping = {
            "invalid_category": ["feature1"]
        }
        valid_mapping, invalid_categories = FeatureServices.validate_mapping(mapping)
        assert valid_mapping == {}
        assert invalid_categories == ["invalid_category"]
    
    def test_mixed_valid_and_invalid_categories(self):
        """Test graceful handling of mixed valid and invalid categories"""
        mapping = {
            "d0_unauth_features": ["credit_score"],
            "invalid_category": ["feature1"],
            "ncr_unauth_features": ["transactions"],
            "another_invalid": ["feature2"]
        }
        valid_mapping, invalid_categories = FeatureServices.validate_mapping(mapping)
        assert "d0_unauth_features" in valid_mapping
        assert "ncr_unauth_features" in valid_mapping
        assert "invalid_category" not in valid_mapping
        assert "another_invalid" not in valid_mapping
        assert set(invalid_categories) == {"invalid_category", "another_invalid"}


class TestValidateItems:
    """Tests for validate_items - only validates business rules (category whitelist)"""
    
    def test_validate_valid_items(self):
        """Test validating valid items with allowed category"""
        items = {
            "d0_unauth_features": {"credit_score": 750, "age": 30}
        }
        # Should not raise exception
        FeatureServices.validate_items(items)
    
    def test_validate_multiple_categories(self):
        """Test validating multiple allowed categories"""
        items = {
            "d0_unauth_features": {"credit_score": 750},
            "ncr_unauth_features": {"transactions": 10}
        }
        # Should not raise exception
        FeatureServices.validate_items(items)
    
    def test_validate_invalid_category(self):
        """Test validating with invalid category (not in whitelist)"""
        items = {
            "invalid_category": {"feature": "value"}
        }
        with pytest.raises(ValueError) as exc_info:
            FeatureServices.validate_items(items)
        assert "not allowed" in str(exc_info.value)



