"""
Unit tests for custom exception hierarchy and error categorization.
"""

import pytest
from botocore.exceptions import ClientError
from core.exceptions import (
    FeatureStoreException,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    InternalServerError,
    ServiceUnavailableError,
    categorize_error
)


class TestCustomExceptions:
    """Tests for custom exception classes"""
    
    def test_feature_store_exception(self):
        """Test base FeatureStoreException"""
        error = FeatureStoreException("Test error", status_code=418)
        assert error.message == "Test error"
        assert error.status_code == 418
        assert str(error) == "Test error"
    
    def test_validation_error(self):
        """Test ValidationError has correct status code"""
        error = ValidationError("Invalid input")
        assert error.status_code == 400
        assert error.message == "Invalid input"
    
    def test_not_found_error(self):
        """Test NotFoundError has correct status code"""
        error = NotFoundError("Resource not found")
        assert error.status_code == 404
        assert error.message == "Resource not found"
    
    def test_conflict_error(self):
        """Test ConflictError has correct status code"""
        error = ConflictError("Data conflict")
        assert error.status_code == 409
        assert error.message == "Data conflict"
    
    def test_unauthorized_error(self):
        """Test UnauthorizedError has correct status code"""
        error = UnauthorizedError("Authentication required")
        assert error.status_code == 401
        assert error.message == "Authentication required"
    
    def test_forbidden_error(self):
        """Test ForbiddenError has correct status code"""
        error = ForbiddenError("Access denied")
        assert error.status_code == 403
        assert error.message == "Access denied"
    
    def test_internal_server_error(self):
        """Test InternalServerError has correct status code"""
        error = InternalServerError("Something went wrong")
        assert error.status_code == 500
        assert error.message == "Something went wrong"
    
    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError has correct status code"""
        error = ServiceUnavailableError("Database down")
        assert error.status_code == 503
        assert error.message == "Database down"


class TestCategorizeError:
    """Tests for error categorization logic"""
    
    def test_already_feature_store_exception(self):
        """Test that FeatureStoreExceptions are returned as-is"""
        original_error = ValidationError("Test validation error")
        result = categorize_error(original_error)
        assert result is original_error
        assert result.status_code == 400
    
    def test_not_found_patterns(self):
        """Test categorization of 'not found' errors"""
        test_cases = [
            ValueError("Item not found"),
            ValueError("Resource does not exist"),
            ValueError("User doesn't exist"),
            ValueError("No items found for query"),
            ValueError("Item not found: user123/category")
        ]
        
        for error in test_cases:
            result = categorize_error(error)
            assert isinstance(result, NotFoundError)
            assert result.status_code == 404
    
    def test_validation_patterns(self):
        """Test categorization of validation errors"""
        test_cases = [
            ValueError("Invalid format"),
            ValueError("Field must be a string"),
            ValueError("Value cannot be empty"),
            ValueError("Missing required field: name"),
            ValueError("Expected integer, got string"),
            ValueError("Value too long (max 100 characters)"),
            ValueError("Category not allowed")
        ]
        
        for error in test_cases:
            result = categorize_error(error)
            assert isinstance(result, ValidationError)
            assert result.status_code == 400
    
    def test_dynamodb_errors(self):
        """Test categorization of DynamoDB/AWS errors"""
        test_cases = [
            ValueError("DynamoDB connection failed"),
            ValueError("AWS service error"),
            ValueError("Boto3 error occurred")
        ]
        
        for error in test_cases:
            result = categorize_error(error)
            assert isinstance(result, ServiceUnavailableError)
            assert result.status_code == 503
    
    def test_forbidden_patterns(self):
        """Test categorization of forbidden/permission errors"""
        test_cases = [
            ValueError("Forbidden resource"),
            ValueError("Permission denied"),
            ValueError("Access denied"),
            ValueError("Unauthorized category")
        ]
        
        for error in test_cases:
            result = categorize_error(error)
            assert isinstance(result, ForbiddenError)
            assert result.status_code == 403
        
        # "Category not allowed" contains "not allowed" which is in validation patterns
        # so it should be ValidationError (400), not ForbiddenError
        not_allowed_error = ValueError("Category not allowed")
        result = categorize_error(not_allowed_error)
        assert isinstance(result, ValidationError)
        assert result.status_code == 400
    
    def test_key_error(self):
        """Test categorization of KeyError as validation error"""
        error = KeyError("missing_field")
        result = categorize_error(error)
        assert isinstance(result, ValidationError)
        assert result.status_code == 400
        assert "missing_field" in result.message
    
    def test_type_error(self):
        """Test categorization of TypeError as validation error"""
        error = TypeError("Expected string, got int")
        result = categorize_error(error)
        assert isinstance(result, ValidationError)
        assert result.status_code == 400
    
    def test_unknown_error(self):
        """Test categorization of unknown errors as internal server error"""
        # Use an error message that doesn't match any validation patterns
        error = RuntimeError("Something broke in the system")
        result = categorize_error(error)
        assert isinstance(result, InternalServerError)
        assert result.status_code == 500
        assert "Unexpected error" in result.message
    
    def test_case_insensitive_matching(self):
        """Test that error message matching is case-insensitive"""
        test_cases = [
            (ValueError("ITEM NOT FOUND"), NotFoundError, 404),
            (ValueError("Invalid Format"), ValidationError, 400),
            (ValueError("PERMISSION DENIED"), ForbiddenError, 403)
        ]
        
        for error, expected_type, expected_code in test_cases:
            result = categorize_error(error)
            assert isinstance(result, expected_type)
            assert result.status_code == expected_code
    
    def test_complex_error_messages(self):
        """Test categorization with complex error messages"""
        # Should match "not found" pattern
        error1 = ValueError("Could not locate item not found in database for user123")
        result1 = categorize_error(error1)
        assert isinstance(result1, NotFoundError)
        assert result1.status_code == 404
        
        # Should match "invalid" pattern
        error2 = ValueError("The provided value is invalid according to schema validation rules")
        result2 = categorize_error(error2)
        assert isinstance(result2, ValidationError)
        assert result2.status_code == 400
    
    def test_empty_error_message(self):
        """Test categorization of errors with empty messages"""
        error = ValueError("")
        result = categorize_error(error)
        # Should default to internal server error
        assert isinstance(result, InternalServerError)
        assert result.status_code == 500


class TestErrorPriority:
    """Test that error categorization prioritizes correctly"""
    
    def test_not_allowed_is_validation(self):
        """Test that 'not allowed' triggers validation error"""
        # "not allowed" is in validation patterns, so should be 400
        error = ValueError("Category not allowed")
        result = categorize_error(error)
        assert isinstance(result, ValidationError)
        assert result.status_code == 400
    
    def test_multiple_pattern_matches(self):
        """Test errors that match multiple patterns"""
        # This message has both "not found" and "invalid"
        error = ValueError("Invalid request: item not found")
        result = categorize_error(error)
        # Should match "not found" first (checked before "invalid")
        assert isinstance(result, NotFoundError)
        assert result.status_code == 404

