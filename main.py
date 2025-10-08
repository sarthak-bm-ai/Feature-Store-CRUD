from fastapi import FastAPI
from api.v1.routes import router
from core.settings import settings
from core.logging_config import setup_logging
from core.exception_handlers import setup_exception_handlers
from middlewares.logging_middleware import setup_logging_middleware
from middlewares.metrics_middleware import setup_metrics_middleware

# Setup logging first
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="Simplified CRUD operations for managing feature data across DynamoDB tables",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Setup exception handlers (must be before middleware)
app = setup_exception_handlers(app)

# Setup middleware (order matters: metrics first, then logging)
app = setup_metrics_middleware(app)
app = setup_logging_middleware(app)

# Include the API v1 router
app.include_router(router, prefix="/api/v1", tags=["features"])
