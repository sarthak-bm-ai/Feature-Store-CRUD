# Feature Store API

A production-ready Feature Store API built with FastAPI and DynamoDB, designed for high-performance feature retrieval and storage with enterprise-grade observability.

## 🚀 Features

### Core Functionality
- ✅ **Feature Storage & Retrieval**: Store and retrieve features with automatic metadata management
- ✅ **Category-based Organization**: Organize features by categories for efficient querying
- ✅ **Wildcard Support**: Retrieve all features in a category using `category:*` pattern
- ✅ **Multi-entity Support**: Support for multiple entity types (`bright_uid`, `account_id`)
- ✅ **Atomic Upserts**: Automatic metadata preservation with `created_at` and `updated_at` tracking

### Production-Ready Features
- 🔐 **Source Validation**: Enforces `source: "prediction_service"` for write operations
- 📊 **Metrics & Monitoring**: Automatic StatsD metrics for all operations
- 📝 **Structured Logging**: Environment-aware logging (JSON for production, colored for development)
- 🌐 **CORS Support**: Configurable cross-origin policies for different environments
- ⚡ **DynamoDB Singleton**: Efficient connection pooling with automatic health checks
- 🔄 **Kafka Events**: Publishes feature availability events with Avro schema serialization
- ✅ **Pydantic Validation**: Type-safe request/response models with automatic API docs
- 🕐 **Timestamp Consistency**: ISO 8601 format with milliseconds across all operations
- 🎯 **Clean Architecture**: Separation of concerns (routes → controllers → services → flows → CRUD)

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Data Models](#data-models)
- [Architecture](#architecture)
- [Monitoring & Logging](#monitoring--logging)
- [Development](#development)
- [Testing](#testing)
- [Documentation](#documentation)

## 🛠 Installation

### Prerequisites
- Python 3.8+
- AWS Account with DynamoDB access
- Kafka cluster (optional, for event publishing)
- StatsD server (optional, for metrics)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Feature-Store-CRUD
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Environment
ENVIRONMENT=development  # development, staging, production

# AWS DynamoDB
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# DynamoDB Tables
DYNAMODB_TABLE_BRIGHT_UID=bright_uid
DYNAMODB_TABLE_ACCOUNT_ID=account_id

# Kafka Configuration (optional)
KAFKA_BROKER_URL=localhost:9092
SCHEMA_REGISTRY=http://localhost:8081
TOPIC_NAME=feature-availability

# Metrics (optional)
STATSD_HOST=localhost
STATSD_PORT=8125
STATSD_PREFIX=feature_store

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### CORS Configuration

CORS is automatically configured based on environment:

- **Development**: Allows all origins (`*`)
- **Staging**: Specific staging domains
- **Production**: Strict production domains only

Edit `middlewares/cors.py` to customize allowed origins.

## 📡 API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### 1. Health Check

**GET** `/health`

Check API and DynamoDB connection health.

**Response:**
```json
{
  "status": "healthy",
  "dynamodb_connection": true,
  "tables_available": ["bright_uid", "account_id"],
  "timestamp": "2025-10-13T09:15:51.358632+00:00"
}
```

### 2. Get Single Category Features

**GET** `/get/item/{entity_value}/{category}`

Retrieve all features for a specific category.

**Parameters:**
- `entity_value` (path): Entity identifier (e.g., user ID)
- `category` (path): Feature category name
- `entity_type` (query, optional): `bright_uid` or `account_id` (default: `bright_uid`)

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/get/item/user-123/user_features?entity_type=bright_uid"
```

**Response:**
```json
{
  "bright_uid": "user-123",
  "category": "user_features",
  "features": {
    "data": {
      "age": 30,
      "income": 60000,
      "city": "SF"
    },
    "meta": {
      "created_at": "2025-10-13T08:12:47.751080+00:00",
      "updated_at": "2025-10-13T08:15:30.123456+00:00",
      "compute_id": "compute-123"
    }
  }
}
```

### 3. Get Multiple Features

**POST** `/get/items`

Retrieve specific features from multiple categories with wildcard support.

**Request Body:**
```json
{
  "meta": {
    "source": "api"
  },
  "data": {
    "entity_type": "bright_uid",
    "entity_value": "user-123",
    "feature_list": [
      "user_features:age",
      "user_features:income",
      "transaction_features:*"
    ]
  }
}
```

**Wildcard Support:**
- `category:*` - Retrieves all features in that category
- `category:feature_name` - Retrieves specific feature

**Response:**
```json
{
  "entity_value": "user-123",
  "entity_type": "bright_uid",
  "items": {
    "user_features": {
      "features": {
        "data": {
          "age": 30,
          "income": 60000
        },
        "metadata": {
          "created_at": "2025-10-13T08:12:47.751080+00:00",
          "updated_at": "2025-10-13T08:15:30.123456+00:00",
          "compute_id": "compute-123"
        }
      }
    },
    "transaction_features": {
      "features": {
        "data": {
          "total_transactions": 150,
          "avg_transaction_value": 250.5
        },
        "metadata": {
          "created_at": "2025-10-13T08:10:00.000000+00:00",
          "updated_at": "2025-10-13T08:20:00.000000+00:00",
          "compute_id": "compute-456"
        }
      }
    }
  },
  "unavailable_feature_categories": []
}
```

### 4. Upsert Features

**POST** `/items`

Write or update features with automatic metadata handling.

**⚠️ Requires:** `source: "prediction_service"` in metadata

**Request Body:**
```json
{
  "metadata": {
    "source": "prediction_service"
  },
  "data": {
    "entity_type": "bright_uid",
    "entity_value": "user-123",
    "feature_list": [
      {
        "category": "user_features",
        "features": {
          "age": 30,
          "income": 60000,
          "city": "SF"
        }
      },
      {
        "category": "credit_features",
        "features": {
          "credit_score": 750,
          "num_accounts": 3
        }
      }
    ]
  }
}
```

**Response:**
```json
{
  "entity_value": "user-123",
  "entity_type": "bright_uid",
  "categories_updated": ["user_features", "credit_features"],
  "timestamp": "2025-10-13T09:15:51.358632+00:00"
}
```

**Features:**
- ✅ Preserves `created_at` on updates
- ✅ Automatically updates `updated_at`
- ✅ Publishes Kafka event after successful write
- ✅ Validates source is `prediction_service`

## 📊 Data Models

### Feature Structure

```python
{
  "features": {
    "data": {
      # Your feature key-value pairs
      "feature1": value1,
      "feature2": value2,
      ...
    },
    "metadata": {
      "created_at": "2025-10-13T08:12:47.751080+00:00",  # ISO 8601 format
      "updated_at": "2025-10-13T08:15:30.123456+00:00",  # ISO 8601 format
      "compute_id": "compute-123"                         # Optional
    }
  }
}
```

### DynamoDB Structure

**Primary Key:**
- Partition Key: `entity_type` (bright_uid or account_id)
- Sort Key: `category`

**Item Structure:**
```json
{
  "bright_uid": "user-123",
  "category": "user_features",
  "features": {
    "data": {
      "age": {"N": "30"},
      "income": {"N": "60000"}
    },
    "metadata": {
      "created_at": {"S": "2025-10-13T08:12:47.751080+00:00"},
      "updated_at": {"S": "2025-10-13T08:15:30.123456+00:00"},
      "compute_id": {"S": "compute-123"}
    }
  }
}
```

### Timestamp Format

All timestamps follow **ISO 8601 format with milliseconds**:
```
Format: YYYY-MM-DDTHH:MM:SS.ffffff+00:00
Example: 2025-10-13T09:15:51.358632+00:00
```

## 🏗 Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│           API Routes (FastAPI)          │  ← HTTP endpoints
├─────────────────────────────────────────┤
│            Controllers                  │  ← Request/response handling
├─────────────────────────────────────────┤
│             Services                    │  ← Validation & sanitization
├─────────────────────────────────────────┤
│              Flows                      │  ← Business logic
├─────────────────────────────────────────┤
│              CRUD                       │  ← DynamoDB operations
└─────────────────────────────────────────┘
```

### Directory Structure

```
Feature-Store-CRUD/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration
│
├── api/                         # API layer
│   └── v1/
│       └── routes.py           # Route definitions
│
├── components/                  # Feature modules
│   └── features/
│       ├── controller.py       # Controller layer
│       ├── services.py         # Service layer
│       ├── flows.py            # Business logic layer
│       ├── crud.py             # DynamoDB operations
│       ├── models.py           # Pydantic models
│       └── schemas.py          # API schemas
│
├── core/                        # Core utilities
│   ├── config.py               # DynamoDB singleton
│   ├── settings.py             # Settings management
│   ├── logging_config.py       # Logging configuration
│   ├── metrics.py              # Metrics utilities
│   ├── timestamp_utils.py      # Timestamp utilities
│   └── kafka_publisher.py      # Kafka event publisher
│
├── middlewares/                 # Middleware
│   ├── logging_middleware.py  # Request/response logging
│   ├── metrics_middleware.py  # HTTP metrics
│   └── cors.py                # CORS configuration
│
└── schemas/                     # Avro schemas
    └── feature_trigger.avsc    # Kafka event schema
```

## 📊 Monitoring & Logging

### Metrics (StatsD)

Automatically tracked metrics:

**HTTP Metrics:**
- `http.request.count` - Total requests
- `http.request.duration` - Request duration
- `http.response.{status_code}` - Response status codes

**Operation Metrics:**
- `read.single_item` - Single category reads
- `read.multi_category` - Multi-category reads
- `write.multi_category` - Feature writes
- `dynamodb.get_item` - DynamoDB GetItem operations
- `dynamodb.put_item` - DynamoDB PutItem operations
- `kafka.publish` - Kafka event publishes

**Tags:**
- `endpoint` - API endpoint path
- `method` - HTTP method
- `status` - Response status code
- `entity_type` - Entity type (bright_uid/account_id)

### Logging

**Development:**
- Colored console output
- Detailed request/response logs
- Pretty-printed JSON

**Production:**
- Structured JSON logs
- Request ID tracking
- Error stack traces
- Performance metrics

**Log Levels:**
- `DEBUG` - Detailed debugging information
- `INFO` - General information (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages with stack traces

### Health Monitoring

Use the `/health` endpoint for monitoring:

```bash
# Check service health
curl http://localhost:8000/api/v1/health

# Integration with monitoring tools
# - Kubernetes liveness/readiness probes
# - Load balancer health checks
# - Uptime monitoring services
```

## 🔧 Development

### Local Development

1. **Start DynamoDB Local** (optional)
```bash
docker run -p 8000:8000 amazon/dynamodb-local
```

2. **Start StatsD Server** (optional)
```bash
python statsd_server.py
```

3. **Run the application**
```bash
source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

4. **Access API documentation**
```
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/redoc     # ReDoc
```

### Code Style

- **Formatting**: Follow PEP 8
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Document all public functions
- **Validation**: Use Pydantic models for data validation

### Adding New Features

1. Define Pydantic models in `components/features/models.py`
2. Add business logic in `components/features/flows.py`
3. Add CRUD operations in `components/features/crud.py`
4. Add route handlers in `api/v1/routes.py`
5. Update documentation

## 🧪 Testing

### Manual Testing

**Test Read Operation:**
```bash
curl -X GET "http://localhost:8000/api/v1/get/item/user-123/user_features?entity_type=bright_uid"
```

**Test Write Operation:**
```bash
curl -X POST "http://localhost:8000/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {"source": "prediction_service"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "user-123",
      "feature_list": [{
        "category": "user_features",
        "features": {"age": 30, "income": 60000}
      }]
    }
  }'
```

**Test Wildcard Retrieval:**
```bash
curl -X POST "http://localhost:8000/api/v1/get/items" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {"source": "api"},
    "data": {
      "entity_type": "bright_uid",
      "entity_value": "user-123",
      "feature_list": ["user_features:*"]
    }
  }'
```

## 📚 Documentation

### Additional Documentation

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Detailed API reference
- **[LOGGING_DOCUMENTATION.md](LOGGING_DOCUMENTATION.md)** - Logging configuration
- **[CLEAN_ARCHITECTURE_IMPLEMENTATION.md](CLEAN_ARCHITECTURE_IMPLEMENTATION.md)** - Architecture details
- **[DYNAMODB_SINGLETON_IMPLEMENTATION.md](DYNAMODB_SINGLETON_IMPLEMENTATION.md)** - DynamoDB connection management
- **[KAFKA_AVRO_IMPLEMENTATION.md](KAFKA_AVRO_IMPLEMENTATION.md)** - Kafka event publishing
- **[TIMESTAMP_CONSISTENCY_IMPLEMENTATION.md](TIMESTAMP_CONSISTENCY_IMPLEMENTATION.md)** - Timestamp handling
- **[PYDANTIC_VALIDATION_IMPLEMENTATION.md](PYDANTIC_VALIDATION_IMPLEMENTATION.md)** - Data validation
- **[DYNAMODB_STRUCTURE_FIX.md](DYNAMODB_STRUCTURE_FIX.md)** - DynamoDB structure optimization

## 🚀 Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Configure production DynamoDB tables
- [ ] Set up Kafka cluster with Schema Registry
- [ ] Configure StatsD/Datadog for metrics
- [ ] Set up log aggregation (CloudWatch, ELK, etc.)
- [ ] Configure CORS allowed origins for production domains
- [ ] Set up health check monitoring
- [ ] Enable AWS IAM roles for DynamoDB access
- [ ] Configure auto-scaling for DynamoDB tables
- [ ] Set up API rate limiting (if needed)

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t feature-store-api .
docker run -p 8000:8000 --env-file .env feature-store-api
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

[Add your license here]

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in the `/docs` folder
- Review the API documentation at `/docs` endpoint

## 🎯 Roadmap

- [ ] Better logic to control writes(only prediction service)
- [ ] AVL for requests routing


---

**Built with ❤️ using FastAPI, DynamoDB, and modern Python best practices.**


