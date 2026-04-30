"""Health and stats endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from api import __version__
from api.database import check_database_health
from api.schemas import CurrentStats, HealthResponse
from api.security import get_rate_limit_for_endpoint, limiter
from database.queries import DatabaseQueries

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["health"], responses={503: {"description": "Unavailable"}})


@router.get("/health", response_model=HealthResponse, summary="Health check")
@limiter.limit(get_rate_limit_for_endpoint("health"))
async def health_check(request: Request) -> HealthResponse:
    _ = request
    if not await check_database_health():
        logger.error("Health check failed: database disconnected")
        raise HTTPException(
            status_code=503,
            detail="Service degraded: Database connection failed",
        )
    return HealthResponse(
        status="healthy",
        database="connected",
        timestamp=datetime.now(),
        version=__version__,
    )


@router.get("/stats/current", response_model=CurrentStats, summary="Current gamification stats")
@limiter.limit(get_rate_limit_for_endpoint("stats"))
async def get_current_stats(request: Request) -> CurrentStats:
    _ = request
    try:
        stats = DatabaseQueries().get_current_stats()
    except Exception as e:
        logger.error("Error retrieving stats: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve statistics: {e}"
        ) from e

    return CurrentStats(
        total_gold=stats.get("total_gold", 0),
        total_xp=stats.get("total_xp", 0),
        current_level=stats.get("current_level", 1),
        xp_in_current_level=stats.get("xp_in_current_level", 0),
        xp_to_next_level=stats.get("xp_to_next_level", 1000),
        events_today=stats.get("events_today", 0),
        total_events=stats.get("total_events", 0),
        rank=stats.get("rank", "Iron"),
        calls_made=stats.get("calls_made", 0),
        calls_connected=stats.get("calls_connected", 0),
        meetings_booked=stats.get("meetings_booked", 0),
    )
