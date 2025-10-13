"""
Centralized timestamp utilities for consistent datetime handling across the service.
All timestamps are stored in ISO 8601 format with milliseconds precision.
"""
from datetime import datetime, timezone
from typing import Optional


def get_current_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format with milliseconds.
    
    Format: YYYY-MM-DDTHH:MM:SS.ffffff+00:00
    Example: 2025-10-13T08:12:47.751080+00:00
    
    Returns:
        str: Current timestamp in ISO 8601 format
    """
    return datetime.now(timezone.utc).isoformat()


def format_timestamp(dt: datetime) -> str:
    """
    Format a datetime object to ISO 8601 string with milliseconds.
    
    Args:
        dt: datetime object (timezone-aware or naive)
        
    Returns:
        str: Formatted timestamp in ISO 8601 format
    """
    # If naive datetime, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse an ISO 8601 timestamp string to datetime object.
    
    Args:
        timestamp_str: ISO 8601 formatted timestamp string
        
    Returns:
        datetime: Parsed datetime object (timezone-aware)
        None: If parsing fails
    """
    try:
        # Try parsing with timezone info
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        try:
            # Try parsing without timezone and add UTC
            dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
            return dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            try:
                # Try parsing without microseconds
                dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
                return dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return None


def validate_timestamp_format(timestamp_str: str) -> bool:
    """
    Validate if a string is in correct ISO 8601 timestamp format.
    
    Args:
        timestamp_str: Timestamp string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return parse_timestamp(timestamp_str) is not None


def ensure_timestamp_consistency(timestamp: any) -> str:
    """
    Ensure timestamp is in consistent ISO 8601 format.
    Handles various input types: datetime, string, or None.
    
    Args:
        timestamp: Input timestamp (datetime object, string, or None)
        
    Returns:
        str: Consistent ISO 8601 formatted timestamp
    """
    if timestamp is None:
        return get_current_timestamp()
    
    if isinstance(timestamp, datetime):
        return format_timestamp(timestamp)
    
    if isinstance(timestamp, str):
        parsed = parse_timestamp(timestamp)
        if parsed:
            return format_timestamp(parsed)
        else:
            # If parsing fails, return current timestamp
            return get_current_timestamp()
    
    # For any other type, return current timestamp
    return get_current_timestamp()


# Constants for timestamp field names
TIMESTAMP_FIELDS = {
    'CREATED_AT': 'created_at',
    'UPDATED_AT': 'updated_at',
    'LAST_ACCESSED_AT': 'last_accessed_at',
    'DELETED_AT': 'deleted_at',
}


def get_timestamp_metadata() -> dict:
    """
    Get standard timestamp metadata for new records.
    
    Returns:
        dict: Dictionary with created_at and updated_at timestamps
    """
    now = get_current_timestamp()
    return {
        TIMESTAMP_FIELDS['CREATED_AT']: now,
        TIMESTAMP_FIELDS['UPDATED_AT']: now,
    }


def get_update_timestamp() -> dict:
    """
    Get timestamp metadata for updates (only updated_at).
    
    Returns:
        dict: Dictionary with updated_at timestamp
    """
    return {
        TIMESTAMP_FIELDS['UPDATED_AT']: get_current_timestamp(),
    }

