import os
import time
import functools
from typing import Optional
from statsd import StatsClient

# StatsD configuration
STATSD_HOST = os.getenv("STATSD_HOST", "localhost")
STATSD_PORT = int(os.getenv("STATSD_PORT", "8125"))
STATSD_PREFIX = os.getenv("STATSD_PREFIX", "feature_store")

# Initialize StatsD client
statsd_client = StatsClient(host=STATSD_HOST, port=STATSD_PORT, prefix=STATSD_PREFIX)

class MetricsCollector:
    """Centralized metrics collection for the feature store."""
    
    def __init__(self, client: StatsClient):
        self.client = client
    
    def increment_counter(self, metric_name: str, value: int = 1, tags: Optional[dict] = None):
        """Increment a counter metric."""
        if tags:
            # Format tags as key=value pairs
            tag_str = ",".join([f"{k}={v}" for k, v in tags.items()])
            metric_name = f"{metric_name},{tag_str}"
        self.client.incr(metric_name, value)
    
    def timing(self, metric_name: str, duration_ms: float, tags: Optional[dict] = None):
        """Record a timing metric in milliseconds."""
        if tags:
            tag_str = ",".join([f"{k}={v}" for k, v in tags.items()])
            metric_name = f"{metric_name},{tag_str}"
        self.client.timing(metric_name, duration_ms)
    
    def gauge(self, metric_name: str, value: float, tags: Optional[dict] = None):
        """Set a gauge metric value."""
        if tags:
            tag_str = ",".join([f"{k}={v}" for k, v in tags.items()])
            metric_name = f"{metric_name},{tag_str}"
        self.client.gauge(metric_name, value)

# Global metrics collector instance
metrics = MetricsCollector(statsd_client)

def time_function(metric_name: str):
    """Decorator to time function execution and record metrics."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # Record success timing
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract relevant tags from kwargs if available
                tags = {}
                if "identifier" in kwargs:
                    tags["identifier"] = kwargs["identifier"]
                if "category" in kwargs:
                    tags["category"] = kwargs["category"]
                if "table_type" in kwargs:
                    tags["table_type"] = kwargs["table_type"]
                
                metrics.timing(f"{metric_name}.duration", duration_ms, tags if tags else None)
                metrics.increment_counter(f"{metric_name}.success", tags=tags if tags else None)
                return result
            except Exception as e:
                # Record error timing and counter
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract relevant tags from kwargs if available
                tags = {}
                if "identifier" in kwargs:
                    tags["identifier"] = kwargs["identifier"]
                if "category" in kwargs:
                    tags["category"] = kwargs["category"]
                if "table_type" in kwargs:
                    tags["table_type"] = kwargs["table_type"]
                
                metrics.timing(f"{metric_name}.duration", duration_ms, tags if tags else None)
                metrics.increment_counter(f"{metric_name}.error", tags=tags if tags else None)
                raise
        return wrapper
    return decorator

# Predefined metric names for consistency
class MetricNames:
    # Read operations
    READ_SINGLE_ITEM = "read.single_item"
    READ_MULTI_CATEGORY = "read.multi_category"
    READ_BY_CATEGORY = "read.by_category"
    
    # Write operations
    WRITE_SINGLE_ITEM = "write.single_item"
    WRITE_MULTI_CATEGORY = "write.multi_category"
    WRITE_BY_CATEGORY = "write.by_category"
    
    # DynamoDB operations
    DYNAMODB_GET_ITEM = "dynamodb.get_item"
    DYNAMODB_PUT_ITEM = "dynamodb.put_item"
    DYNAMODB_UPDATE_ITEM = "dynamodb.update_item"
    
    # General
    HTTP_REQUEST = "http.request"
    HTTP_ERROR = "http.error"
