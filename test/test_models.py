"""
Unit tests for Pydantic models
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from components.features.models import (
    FeatureMeta, Features, Item, RequestMeta, WriteRequestMeta,
    ReadRequest, WriteRequest, ReadResponse, WriteResponse,
    HealthResponse, ErrorResponse
)


class TestFeatureMeta:
    """Tests for FeatureMeta model"""
    
    def test_feature_meta_creation(self):
        """Test creating FeatureMeta with valid data"""
        meta = FeatureMeta(
            created_at="2025-10-14T12:34:56.789Z",
            updated_at="2025-10-14T12:34:56.789Z",
            compute_id="test-compute-id"
        )
        assert meta.compute_id == "test-compute-id"
        assert isinstance(meta.created_at, datetime)
        assert isinstance(meta.updated_at, datetime)
    
    def test_feature_meta_without_compute_id(self):
        """Test FeatureMeta with None compute_id"""
        meta = FeatureMeta(
            created_at="2025-10-14T12:34:56.789Z",
            updated_at="2025-10-14T12:34:56.789Z"
        )
        assert meta.compute_id is None
    
    def test_feature_meta_timestamp_parsing(self):
        """Test various timestamp format parsing"""
        formats = [
            "2025-10-14T12:34:56.789Z",
            "2025-10-14T12:34:56Z",
            "2025-10-14T12:34:56.789+00:00",
            "2025-10-14 12:34:56.789"
        ]
        for ts_format in formats:
            meta = FeatureMeta(
                created_at=ts_format,
                updated_at=ts_format
            )
            assert isinstance(meta.created_at, datetime)


class TestFeatures:
    """Tests for Features model"""
    
    def test_features_creation(self):
        """Test creating Features with valid data"""
        features = Features(
            data={"credit_score": 750, "age": 30},
            meta=FeatureMeta(
                created_at="2025-10-14T12:34:56.789Z",
                updated_at="2025-10-14T12:34:56.789Z"
            )
        )
        assert features.data == {"credit_score": 750, "age": 30}
        assert isinstance(features.meta, FeatureMeta)
    
    def test_features_with_empty_data(self):
        """Test Features with empty data dict"""
        features = Features(
            data={},
            meta=FeatureMeta(
                created_at="2025-10-14T12:34:56.789Z",
                updated_at="2025-10-14T12:34:56.789Z"
            )
        )
        assert features.data == {}


class TestRequestMeta:
    """Tests for RequestMeta model"""
    
    def test_request_meta_creation(self):
        """Test creating RequestMeta"""
        meta = RequestMeta(source="api")
        assert meta.source == "api"
    
    def test_request_meta_validation(self):
        """Test RequestMeta requires source"""
        with pytest.raises(ValidationError):
            RequestMeta()


class TestWriteRequestMeta:
    """Tests for WriteRequestMeta model"""
    
    def test_write_request_meta_prediction_service(self):
        """Test WriteRequestMeta with prediction_service"""
        meta = WriteRequestMeta(source="prediction_service")
        assert meta.source == "prediction_service"
        assert meta.compute_id is None
    
    def test_write_request_meta_with_compute_id(self):
        """Test WriteRequestMeta with compute_id"""
        meta = WriteRequestMeta(source="prediction_service", compute_id="test-compute-123")
        assert meta.source == "prediction_service"
        assert meta.compute_id == "test-compute-123"
    
    def test_write_request_meta_invalid_source(self):
        """Test WriteRequestMeta rejects invalid source"""
        with pytest.raises(ValidationError) as exc_info:
            WriteRequestMeta(source="invalid_source")
        assert "prediction_service" in str(exc_info.value)


class TestWriteRequest:
    """Tests for WriteRequest model (single category writes)"""
    
    def test_write_request_valid(self):
        """Test valid WriteRequest with single category"""
        request = WriteRequest(
            meta=WriteRequestMeta(source="prediction_service"),
            data={
                "entity_type": "bright_uid",
                "entity_value": "test-123",
                "category": "d0_unauth_features",
                "features": {"credit_score": 750}
            }
        )
        assert request.data["entity_type"] == "bright_uid"
        assert request.data["entity_value"] == "test-123"
        assert request.data["category"] == "d0_unauth_features"
        assert request.data["features"] == {"credit_score": 750}
    
    def test_write_request_invalid_entity_type(self):
        """Test WriteRequest with invalid entity_type"""
        with pytest.raises(ValidationError) as exc_info:
            WriteRequest(
                meta=WriteRequestMeta(source="prediction_service"),
                data={
                    "entity_type": "invalid_type",
                    "entity_value": "test-123",
                    "category": "d0_unauth_features",
                    "features": {"credit_score": 750}
                }
            )
        assert "entity_type" in str(exc_info.value)
    
    def test_write_request_missing_fields(self):
        """Test WriteRequest with missing required fields"""
        with pytest.raises(ValidationError):
            WriteRequest(
                meta=WriteRequestMeta(source="prediction_service"),
                data={
                    "entity_type": "bright_uid"
                }
            )


class TestReadRequest:
    """Tests for ReadRequest model"""
    
    def test_read_request_valid(self):
        """Test valid ReadRequest"""
        request = ReadRequest(
            meta=RequestMeta(source="api"),
            data={
                "entity_type": "bright_uid",
                "entity_value": "test-123",
                "feature_list": ["d0_unauth_features:credit_score"]
            }
        )
        assert request.data["entity_type"] == "bright_uid"
        assert "d0_unauth_features:credit_score" in request.data["feature_list"]
    
    def test_read_request_with_wildcard(self):
        """Test ReadRequest with wildcard feature"""
        request = ReadRequest(
            meta=RequestMeta(source="api"),
            data={
                "entity_type": "bright_uid",
                "entity_value": "test-123",
                "feature_list": ["d0_unauth_features:*"]
            }
        )
        assert "d0_unauth_features:*" in request.data["feature_list"]
    
    def test_read_request_invalid_feature_format(self):
        """Test ReadRequest with invalid feature format"""
        with pytest.raises(ValidationError) as exc_info:
            ReadRequest(
                meta=RequestMeta(source="api"),
                data={
                    "entity_type": "bright_uid",
                    "entity_value": "test-123",
                    "feature_list": ["invalid_format"]
                }
            )
        assert "category:feature" in str(exc_info.value)


class TestWriteResponse:
    """Tests for WriteResponse model (single category writes)"""
    
    def test_write_response_creation(self):
        """Test creating WriteResponse for single category"""
        response = WriteResponse(
            message="Category written successfully (full replace)",
            entity_type="bright_uid",
            entity_value="test-123",
            category="d0_unauth_features",
            feature_count=3
        )
        assert response.message == "Category written successfully (full replace)"
        assert response.category == "d0_unauth_features"
        assert response.feature_count == 3


class TestReadResponse:
    """Tests for ReadResponse model"""
    
    def test_read_response_creation(self):
        """Test creating ReadResponse"""
        response = ReadResponse(
            entity_type="bright_uid",
            entity_value="test-123",
            items={
                "d0_unauth_features": Item(
                    category="d0_unauth_features",
                    features=Features(
                        data={"credit_score": 750},
                        meta=FeatureMeta(
                            created_at="2025-10-14T12:34:56.789Z",
                            updated_at="2025-10-14T12:34:56.789Z",
                            compute_id=None
                        )
                    )
                )
            },
            unavailable_feature_categories=[]
        )
        assert response.entity_type == "bright_uid"
        assert "d0_unauth_features" in response.items
    
    def test_read_response_with_unavailable_categories(self):
        """Test ReadResponse with unavailable categories"""
        response = ReadResponse(
            entity_type="bright_uid",
            entity_value="test-123",
            items={},
            unavailable_feature_categories=["missing_category"]
        )
        assert "missing_category" in response.unavailable_feature_categories


class TestHealthResponse:
    """Tests for HealthResponse model"""
    
    def test_health_response_healthy(self):
        """Test healthy response"""
        response = HealthResponse(
            status="healthy",
            dynamodb_connection=True,
            tables_available=["feature_store_bright_uid"],
            timestamp="2025-10-14T12:34:56.789Z"
        )
        assert response.status == "healthy"
        assert response.dynamodb_connection is True
    
    def test_health_response_unhealthy(self):
        """Test unhealthy response"""
        response = HealthResponse(
            status="unhealthy",
            dynamodb_connection=False,
            tables_available=[],
            timestamp="2025-10-14T12:34:56.789Z"
        )
        assert response.status == "unhealthy"
        assert response.dynamodb_connection is False


class TestErrorResponse:
    """Tests for ErrorResponse model"""
    
    def test_error_response_creation(self):
        """Test creating ErrorResponse"""
        response = ErrorResponse(
            detail="Error message",
            timestamp="2025-10-14T12:34:56.789Z"
        )
        assert response.detail == "Error message"



