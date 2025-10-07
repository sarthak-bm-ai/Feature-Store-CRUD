# Environment-Based Configuration

## Overview
The application now uses environment-based configuration instead of hardcoded values, allowing for easy deployment across different environments (development, staging, production).

## Configuration Files

### Base Configuration (`.env`)
```bash
# AWS Configuration
AWS_REGION=us-west-2
TABLE_NAME_BRIGHT_UID=featuers_poc
TABLE_NAME_ACCOUNT_ID=features_account_id

# StatsD Configuration
STATSD_HOST=localhost
STATSD_PORT=8125
STATSD_PREFIX=feature_store

# Application Configuration
ENVIRONMENT=development
```

### Environment-Specific Configurations

#### Development (`.env.development`)
```bash
# Development Environment Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# AWS Configuration
AWS_REGION=us-west-2
TABLE_NAME_BRIGHT_UID=featuers_poc
TABLE_NAME_ACCOUNT_ID=features_account_id

# StatsD Configuration
STATSD_HOST=localhost
STATSD_PORT=8125
STATSD_PREFIX=feature_store_dev

# Application Configuration
APP_NAME=Feature Store API (Dev)
APP_VERSION=1.0.0-dev
```

#### Staging (`.env.staging`)
```bash
# Staging Environment Configuration
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# AWS Configuration
AWS_REGION=us-west-2
TABLE_NAME_BRIGHT_UID=features_staging_bright_uid
TABLE_NAME_ACCOUNT_ID=features_staging_account_id

# StatsD Configuration
STATSD_HOST=statsd-staging.example.com
STATSD_PORT=8125
STATSD_PREFIX=feature_store_staging

# Application Configuration
APP_NAME=Feature Store API (Staging)
APP_VERSION=1.0.0-staging
```

#### Production (`.env.production`)
```bash
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# AWS Configuration
AWS_REGION=us-west-2
TABLE_NAME_BRIGHT_UID=features_prod_bright_uid
TABLE_NAME_ACCOUNT_ID=features_prod_account_id

# StatsD Configuration
STATSD_HOST=statsd-prod.example.com
STATSD_PORT=8125
STATSD_PREFIX=feature_store_prod

# Application Configuration
APP_NAME=Feature Store API
APP_VERSION=1.0.0
```

## Configuration Loading Priority

1. **Environment-specific file**: `.env.{ENVIRONMENT}` (highest priority)
2. **Base file**: `.env`
3. **Default values**: Hardcoded in `core/settings.py`

## Usage

### Running in Different Environments

#### Development
```bash
# Uses .env.development automatically
python main.py
```

#### Staging
```bash
# Uses .env.staging
ENVIRONMENT=staging python main.py
```

#### Production
```bash
# Uses .env.production
ENVIRONMENT=production python main.py
```

### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.9-slim

# Copy environment-specific config
COPY .env.production /app/.env

# Set environment
ENV ENVIRONMENT=production

# Run application
CMD ["python", "main.py"]
```

### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feature-store-api
spec:
  template:
    spec:
      containers:
      - name: feature-store-api
        image: feature-store-api:latest
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: AWS_REGION
          value: "us-west-2"
        - name: TABLE_NAME_BRIGHT_UID
          value: "features_prod_bright_uid"
```

## Configuration Variables

### AWS Configuration
- `AWS_REGION`: AWS region for DynamoDB
- `TABLE_NAME_BRIGHT_UID`: DynamoDB table name for bright_uid partition key
- `TABLE_NAME_ACCOUNT_ID`: DynamoDB table name for account_id partition key

### StatsD Configuration
- `STATSD_HOST`: StatsD server hostname
- `STATSD_PORT`: StatsD server port
- `STATSD_PREFIX`: Prefix for all metrics

### Application Configuration
- `ENVIRONMENT`: Current environment (development/staging/production)
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `APP_NAME`: Application name
- `APP_VERSION`: Application version

## Benefits

### 1. **Environment Isolation**
- Different configurations for each environment
- No hardcoded values in code
- Easy to change settings without code changes

### 2. **Security**
- Sensitive values can be set via environment variables
- No secrets in version control
- Easy to rotate credentials

### 3. **Deployment Flexibility**
- Same codebase for all environments
- Environment-specific settings
- Easy to add new environments

### 4. **Development Experience**
- Clear separation of concerns
- Easy to test different configurations
- Consistent across team members

## Best Practices

### 1. **Environment Files**
- Keep `.env` files out of version control
- Use `.env.example` as a template
- Document all required variables

### 2. **Default Values**
- Always provide sensible defaults
- Use environment-specific overrides
- Validate required variables on startup

### 3. **Security**
- Never commit secrets to version control
- Use environment variables for sensitive data
- Rotate credentials regularly

### 4. **Documentation**
- Document all configuration variables
- Provide examples for each environment
- Keep configuration files up to date

## Example Usage in Code

```python
from core.settings import settings

# Access configuration
print(f"Running in {settings.ENVIRONMENT} mode")
print(f"Using table: {settings.TABLE_NAME_BRIGHT_UID}")

# Environment checks
if settings.is_production():
    # Production-specific logic
    pass
elif settings.is_development():
    # Development-specific logic
    pass

# Get table name dynamically
table_name = settings.get_table_name("bright_uid")
```

## Migration from Hardcoded Values

### Before
```python
AWS_REGION = "us-west-2"
TABLE_NAME_BRIGHT_UID = "featuers_poc"
STATSD_HOST = "localhost"
```

### After
```python
from core.settings import settings

AWS_REGION = settings.AWS_REGION
TABLE_NAME_BRIGHT_UID = settings.TABLE_NAME_BRIGHT_UID
STATSD_HOST = settings.STATSD_HOST
```

## Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check if `.env` file exists
   - Verify `ENVIRONMENT` variable is set
   - Check file permissions

2. **Wrong environment loaded**
   - Verify `ENVIRONMENT` variable
   - Check if environment-specific file exists
   - Check configuration loading order

3. **Missing variables**
   - Check if variable is defined in environment file
   - Verify default values in `settings.py`
   - Check for typos in variable names

### Debug Configuration Loading
```python
from core.config_loader import load_environment_config
environment = load_environment_config()
print(f"Loaded environment: {environment}")
```
