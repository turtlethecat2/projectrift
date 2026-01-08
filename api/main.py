"""
Project Rift API - Main Application Entry Point
FastAPI application for SDR gamification engine
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api import __version__
from api.config import settings
from api.security import limiter
from api.database import cleanup_database_connections
from api.routers import webhook, health

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events

    Handles:
    - Application startup logging
    - Database connection cleanup on shutdown
    """
    # Startup
    logger.info(f"Starting Project Rift API v{__version__}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"Rate limit: {settings.RATE_LIMIT_PER_MINUTE} requests/minute")

    yield

    # Shutdown
    logger.info("Shutting down Project Rift API")
    cleanup_database_connections()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Project Rift API",
    description="SDR Gamification Engine - Webhook ingestion and stats API",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None
)

# Add rate limiter state
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:8501",  # Streamlit default port
    ] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-RIFT-SECRET", "X-API-KEY"],
)


# Custom exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for uncaught exceptions

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__,
            "path": str(request.url)
        }
    )


# Include routers
app.include_router(webhook.router)
app.include_router(health.router)


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="API root",
    description="Get basic API information"
)
async def root():
    """
    Root endpoint with API information

    Returns:
        Dictionary with API metadata
    """
    return {
        "name": "Project Rift API",
        "version": __version__,
        "description": "SDR Gamification Engine",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "disabled",
        "health": "/api/v1/health",
        "endpoints": {
            "webhook_ingest": "/api/v1/webhook/ingest",
            "current_stats": "/api/v1/stats/current"
        }
    }


# Additional middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all incoming requests

    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler

    Returns:
        Response from next handler
    """
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
