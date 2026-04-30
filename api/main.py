"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api import __version__
from api.config import settings
from api.database import cleanup_database_connections
from api.routers import auth, health, outreach, webhook
from api.scheduler import start_scheduler, stop_scheduler
from api.security import limiter

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Project Rift API v%s", __version__)
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Database: %s:%s/%s", settings.DB_HOST, settings.DB_PORT, settings.DB_NAME)
    logger.info("Rate limit: %s requests/minute", settings.RATE_LIMIT_PER_MINUTE)
    start_scheduler()

    yield

    logger.info("Shutting down Project Rift API")
    stop_scheduler()
    cleanup_database_connections()
    logger.info("Database connections closed")


app = FastAPI(
    title="Project Rift API",
    description="SDR gamification — webhook ingestion and stats API",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_DEV_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8501",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEV_ORIGINS if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-RIFT-SECRET", "X-API-KEY"],
)


app.include_router(webhook.router)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(outreach.router)


@app.get("/", tags=["root"], summary="API root")
async def root():
    return {
        "name": "Project Rift API",
        "version": __version__,
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "disabled",
        "health": "/api/v1/health",
        "webhook_ingest": "/api/v1/webhook/ingest",
        "current_stats": "/api/v1/stats/current",
    }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug("%s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.debug("Response status: %s", response.status_code)
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
