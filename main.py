from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from api.v1.routes import router
from core.settings import settings
from core.logging_config import setup_logging, get_logger
from middlewares.logging_middleware import setup_logging_middleware
from middlewares.metrics_middleware import setup_metrics_middleware
from middlewares.cors import setup_cors_middleware

# Setup logging first
setup_logging()

# Get logger for global exception handling
logger = get_logger("main")

app = FastAPI(
    title=settings.APP_NAME,
    description="Simplified CRUD operations for managing feature data across DynamoDB tables",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Setup middleware (order matters: CORS first, then metrics, then logging)
app = setup_cors_middleware(app)
app = setup_metrics_middleware(app)
app = setup_logging_middleware(app)

# Include the API v1 router
app.include_router(router, prefix="/api/v1", tags=["features"])
