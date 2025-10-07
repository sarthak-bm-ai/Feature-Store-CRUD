# Request/Response Logging Middleware Documentation

## Overview
Comprehensive request/response logging middleware for the Feature Store API that provides detailed visibility into HTTP traffic, request/response details, and performance metrics.

## Features

### 🔍 **Request Logging**
- **Method & Path**: HTTP method and URL path
- **Query Parameters**: All query string parameters
- **Headers**: Request headers (including User-Agent, Content-Type)
- **Client IP**: Source IP address
- **Request Body**: Body content for POST/PUT requests (with size limits)
- **Request ID**: Unique identifier for request tracing

### 📤 **Response Logging**
- **Status Code**: HTTP response status
- **Duration**: Request processing time in milliseconds
- **Content Type**: Response content type
- **Response Headers**: All response headers
- **Response Body**: Response content (with size limits)
- **Performance Metrics**: Detailed timing information

### 🎨 **Environment-Specific Formatting**
- **Development**: Colored, human-readable logs with emojis
- **Production**: Structured JSON logs for log aggregation
- **Staging**: JSON logs with detailed information

## Implementation

### Core Components

#### 1. **Logging Middleware** (`middlewares/logging_middleware.py`)
```python
class RequestResponseLogger:
    """Middleware for logging HTTP requests and responses."""
    
    async def __call__(self, request: Request, call_next):
        # Log request details
        await self._log_request(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        # Log response details
        await self._log_response(request, response, duration, request_id)
        
        return response
```

#### 2. **Logging Configuration** (`core/logging_config.py`)
```python
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
class ColoredFormatter(logging.Formatter):
    """Colored formatter for development environment."""
```

#### 3. **Integration** (`main.py`)
```python
from core.logging_config import setup_logging
from middlewares.logging_middleware import setup_logging_middleware

# Setup logging first
setup_logging()

# Setup logging middleware
app = setup_logging_middleware(app)
```

## Log Examples

### Development Environment (Colored)
```
2025-10-07 12:42:19 - feature_store.middleware - INFO - 📥 REQUEST [a1b2c3d4] POST /api/v1/items/logging-test-001
2025-10-07 12:42:19 - feature_store.middleware - INFO - 📤 RESPONSE [a1b2c3d4] 200 in 0.15s
```

### Production Environment (JSON)
```json
{
  "timestamp": "2025-10-07T12:42:19.123456",
  "level": "INFO",
  "logger": "feature_store.middleware",
  "message": "REQUEST [a1b2c3d4] POST /api/v1/items/logging-test-001",
  "request_id": "a1b2c3d4",
  "method": "POST",
  "path": "/api/v1/items/logging-test-001",
  "client_ip": "127.0.0.1",
  "status_code": 200,
  "duration_ms": 150.25
}
```

## Configuration

### Environment Variables
```bash
# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENVIRONMENT=development           # development, staging, production
DEBUG=true                        # Enable debug mode
```

### Log Levels by Environment
| Environment | Log Level | Format | Features |
|-------------|-----------|--------|----------|
| **Development** | DEBUG | Colored | Emojis, detailed info, request/response bodies |
| **Staging** | INFO | JSON | Structured logs, performance metrics |
| **Production** | WARNING | JSON | Minimal logs, error focus |

## Request/Response Details

### Request Logging
```python
request_log = {
    "request_id": "a1b2c3d4",
    "type": "request",
    "method": "POST",
    "path": "/api/v1/items/user123",
    "query_params": {"table_type": "bright_uid"},
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.68.0",
    "headers": {...},
    "body": '{"test_features": {"feature1": "value"}}',
    "timestamp": 1696675339.123456
}
```

### Response Logging
```python
response_log = {
    "request_id": "a1b2c3d4",
    "type": "response",
    "method": "POST",
    "path": "/api/v1/items/user123",
    "status_code": 200,
    "duration_ms": 150.25,
    "content_type": "application/json",
    "headers": {...},
    "body": '{"message": "Items written successfully"}',
    "timestamp": 1696675339.273456
}
```

## Performance Monitoring

### Duration Tracking
- **Request Start**: Timestamp when request arrives
- **Request End**: Timestamp when response is sent
- **Duration**: Calculated in milliseconds
- **Performance Alerts**: Automatic detection of slow requests

### Status Code Monitoring
- **Success (2xx)**: INFO level logging
- **Client Errors (4xx)**: WARNING level logging
- **Server Errors (5xx)**: ERROR level logging

## Security Considerations

### Sensitive Data Protection
- **Body Size Limits**: Large request/response bodies are truncated
- **Header Filtering**: Sensitive headers can be filtered out
- **IP Logging**: Client IP addresses are logged for security analysis

### Log Retention
- **Development**: Logs kept locally for debugging
- **Production**: Logs sent to centralized logging system
- **Compliance**: Logs can be configured for audit requirements

## Debugging Features

### Request Tracing
- **Unique Request ID**: Each request gets a unique identifier
- **Request Chain**: Track requests through the system
- **Error Correlation**: Link errors to specific requests

### Performance Analysis
- **Slow Request Detection**: Identify requests taking too long
- **Resource Usage**: Monitor memory and CPU usage per request
- **Bottleneck Identification**: Find performance bottlenecks

## Integration with Monitoring

### StatsD Integration
```python
# Metrics are automatically sent to StatsD
metrics.increment_counter("http.request", tags={
    "method": "POST",
    "path": "/api/v1/items",
    "status_code": "200"
})
```

### Log Aggregation
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **CloudWatch**: AWS CloudWatch Logs
- **Splunk**: Enterprise log management
- **Datadog**: Application performance monitoring

## Usage Examples

### Basic Request Logging
```bash
# Development - Colored output
curl -X POST "http://127.0.0.1:8000/api/v1/items/user123" \
  -H "Content-Type: application/json" \
  -d '{"test_features": {"feature1": "value"}}'

# Output:
# 📥 REQUEST [a1b2c3d4] POST /api/v1/items/user123
# 📤 RESPONSE [a1b2c3d4] 200 in 0.15s
```

### Error Logging
```bash
# 404 Error
curl "http://127.0.0.1:8000/api/v1/get/item/nonexistent-user/nonexistent-category"

# Output:
# 📥 REQUEST [b2c3d4e5] GET /api/v1/get/item/nonexistent-user/nonexistent-category
# 📤 RESPONSE [b2c3d4e5] 404 in 0.05s
```

### Performance Monitoring
```bash
# Slow request detection
# 📥 REQUEST [c3d4e5f6] POST /api/v1/items/user123
# 📤 RESPONSE [c3d4e5f6] 200 in 2.5s  # <-- Slow request detected
```

## Best Practices

### 1. **Log Levels**
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Something unexpected happened
- **ERROR**: Error occurred but application continues
- **CRITICAL**: Serious error, application may stop

### 2. **Performance**
- **Async Logging**: Non-blocking log operations
- **Batch Processing**: Group log entries for efficiency
- **Size Limits**: Prevent log files from growing too large

### 3. **Security**
- **Data Sanitization**: Remove sensitive information
- **Access Control**: Restrict log access
- **Encryption**: Encrypt logs in transit and at rest

### 4. **Monitoring**
- **Alerting**: Set up alerts for errors and performance issues
- **Dashboards**: Create visualizations of log data
- **Trends**: Monitor log trends over time

## Troubleshooting

### Common Issues

1. **Logs Not Appearing**
   - Check log level configuration
   - Verify logger configuration
   - Check file permissions

2. **Performance Impact**
   - Reduce log level in production
   - Use async logging
   - Limit request/response body logging

3. **Log File Size**
   - Implement log rotation
   - Use log compression
   - Archive old logs

### Debug Commands
```bash
# Check log configuration
python -c "from core.logging_config import setup_logging; setup_logging()"

# Test logging middleware
curl -v "http://127.0.0.1:8000/api/v1/get/item/test-user/test-category"

# Monitor logs in real-time
tail -f logs/application.log
```

## Future Enhancements

### Planned Features
- **Request Correlation**: Link related requests
- **User Tracking**: Track user-specific requests
- **Custom Fields**: Add custom log fields
- **Log Sampling**: Sample logs in high-traffic scenarios

### Integration Opportunities
- **APM Tools**: New Relic, AppDynamics
- **Error Tracking**: Sentry, Rollbar
- **Performance Monitoring**: DataDog, New Relic
- **Security Monitoring**: SIEM integration

The logging middleware provides comprehensive visibility into the Feature Store API, enabling effective debugging, monitoring, and performance optimization! 🚀
