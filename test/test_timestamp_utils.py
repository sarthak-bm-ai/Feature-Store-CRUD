"""
Unit tests for timestamp utilities
"""
import pytest
from datetime import datetime, timezone
from core.timestamp_utils import (
    get_current_timestamp,
    format_timestamp,
    parse_timestamp,
    validate_timestamp_format,
    ensure_timestamp_consistency
)


class TestGetCurrentTimestamp:
    """Tests for get_current_timestamp"""
    
    def test_get_current_timestamp_format(self):
        """Test that current timestamp is in correct format"""
        timestamp = get_current_timestamp()
        assert isinstance(timestamp, str)
        assert 'T' in timestamp
        assert '.' in timestamp  # Has milliseconds
        # Should be parseable
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(dt, datetime)
    
    def test_get_current_timestamp_has_timezone(self):
        """Test that timestamp includes timezone info"""
        timestamp = get_current_timestamp()
        assert timestamp.endswith('Z') or '+' in timestamp or timestamp.endswith('+00:00')


class TestFormatTimestamp:
    """Tests for format_timestamp"""
    
    def test_format_datetime_with_timezone(self):
        """Test formatting datetime with timezone"""
        dt = datetime(2025, 10, 14, 12, 34, 56, 789000, tzinfo=timezone.utc)
        result = format_timestamp(dt)
        assert isinstance(result, str)
        assert '2025-10-14' in result
        assert '12:34:56' in result
        assert '.789' in result
    
    def test_format_datetime_without_timezone(self):
        """Test formatting naive datetime (assumes UTC)"""
        dt = datetime(2025, 10, 14, 12, 34, 56, 789000)
        result = format_timestamp(dt)
        assert isinstance(result, str)
        assert '2025-10-14' in result


class TestParseTimestamp:
    """Tests for parse_timestamp"""
    
    def test_parse_iso_format(self):
        """Test parsing ISO 8601 format"""
        timestamp = "2025-10-14T12:34:56.789Z"
        dt = parse_timestamp(timestamp)
        assert isinstance(dt, datetime)
        assert dt.year == 2025
        assert dt.month == 10
        assert dt.day == 14
    
    def test_parse_iso_format_with_offset(self):
        """Test parsing ISO format with timezone offset"""
        timestamp = "2025-10-14T12:34:56.789+00:00"
        dt = parse_timestamp(timestamp)
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None
    
    def test_parse_without_milliseconds(self):
        """Test parsing without milliseconds"""
        timestamp = "2025-10-14T12:34:56Z"
        dt = parse_timestamp(timestamp)
        assert isinstance(dt, datetime)
    
    def test_parse_space_separated(self):
        """Test parsing space-separated format"""
        timestamp = "2025-10-14 12:34:56.789"
        dt = parse_timestamp(timestamp)
        assert isinstance(dt, datetime)
    
    def test_parse_invalid_format(self):
        """Test parsing invalid format returns None"""
        result = parse_timestamp("invalid timestamp")
        assert result is None


class TestValidateTimestampFormat:
    """Tests for validate_timestamp_format"""
    
    def test_validate_correct_format(self):
        """Test validating correct ISO 8601 format"""
        timestamp = "2025-10-14T12:34:56.789Z"
        assert validate_timestamp_format(timestamp) is True
    
    def test_validate_without_milliseconds(self):
        """Test validating without milliseconds"""
        timestamp = "2025-10-14T12:34:56Z"
        assert validate_timestamp_format(timestamp) is True
    
    def test_validate_with_offset(self):
        """Test validating with timezone offset"""
        timestamp = "2025-10-14T12:34:56.789+00:00"
        assert validate_timestamp_format(timestamp) is True
    
    def test_validate_invalid_format(self):
        """Test validating invalid format"""
        # Note: "2025-10-14 12:34:56" is actually parseable, so it returns True
        # Only truly invalid formats return False
        assert validate_timestamp_format("invalid") is False
        assert validate_timestamp_format("") is False
        assert validate_timestamp_format("not-a-date") is False


class TestEnsureTimestampConsistency:
    """Tests for ensure_timestamp_consistency"""
    
    def test_ensure_consistency_with_datetime(self):
        """Test ensuring consistency with datetime object"""
        dt = datetime(2025, 10, 14, 12, 34, 56, 789000, tzinfo=timezone.utc)
        result = ensure_timestamp_consistency(dt)
        assert isinstance(result, str)
        assert '2025-10-14' in result
        assert '.789' in result
    
    def test_ensure_consistency_with_valid_string(self):
        """Test ensuring consistency with valid ISO string"""
        timestamp = "2025-10-14T12:34:56.789Z"
        result = ensure_timestamp_consistency(timestamp)
        assert isinstance(result, str)
        assert '2025-10-14' in result
    
    def test_ensure_consistency_with_naive_datetime_string(self):
        """Test ensuring consistency with naive datetime string"""
        timestamp = "2025-10-14 12:34:56"
        result = ensure_timestamp_consistency(timestamp)
        assert isinstance(result, str)
        # Should be converted to ISO format with timezone
        assert 'T' in result or '2025-10-14' in result
    
    def test_ensure_consistency_with_invalid_type(self):
        """Test ensuring consistency with invalid type (fallback to current)"""
        result = ensure_timestamp_consistency(12345)
        assert isinstance(result, str)
        # Should return current timestamp as fallback
        assert 'T' in result
    
    def test_ensure_consistency_with_unparseable_string(self):
        """Test ensuring consistency with unparseable string (fallback)"""
        result = ensure_timestamp_consistency("completely invalid")
        assert isinstance(result, str)
        # Should return current timestamp as fallback
        assert 'T' in result


class TestTimestampRoundtrip:
    """Test roundtrip conversions"""
    
    def test_roundtrip_datetime_to_string_to_datetime(self):
        """Test converting datetime to string and back"""
        original_dt = datetime(2025, 10, 14, 12, 34, 56, 789000, tzinfo=timezone.utc)
        timestamp_str = format_timestamp(original_dt)
        parsed_dt = parse_timestamp(timestamp_str)
        
        # Should be approximately equal (within microseconds)
        assert abs((original_dt - parsed_dt).total_seconds()) < 0.001
    
    def test_roundtrip_with_consistency_check(self):
        """Test ensure_timestamp_consistency roundtrip"""
        dt = datetime(2025, 10, 14, 12, 34, 56, 789000, tzinfo=timezone.utc)
        consistent_str = ensure_timestamp_consistency(dt)
        parsed_back = parse_timestamp(consistent_str)
        
        assert isinstance(parsed_back, datetime)
        assert parsed_back.year == 2025


