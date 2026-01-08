"""
Health check and statistics endpoints
Provides system status and performance metrics
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from api.schemas import HealthResponse, CurrentStats
from api.security import limiter, get_rate_limit_for_endpoint
from api.database import check_database_health
from database.queries import DatabaseQueries
from api import __version__

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["health"],
    responses={
        503: {"description": "Service Unavailable - System unhealthy"}
    }
)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System health check",
    description="Check the health status of the API and database"
)
@limiter.limit(get_rate_limit_for_endpoint("health"))
async def health_check() -> HealthResponse:
    """
    Check system health

    Verifies:
    - API is running
    - Database is accessible
    - System time is correct

    Returns:
        HealthResponse with status information

    Raises:
        HTTPException: 503 if system is unhealthy
    """
    try:
        # Check database connectivity
        db_healthy = await check_database_health()
        db_status = "connected" if db_healthy else "disconnected"

        # Determine overall health
        overall_status = "healthy" if db_healthy else "degraded"

        response = HealthResponse(
            status=overall_status,
            database=db_status,
            timestamp=datetime.now(),
            version=__version__
        )

        # If database is down, return 503
        if not db_healthy:
            logger.error("Health check failed: Database disconnected")
            raise HTTPException(
                status_code=503,
                detail="Service degraded: Database connection failed"
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/stats/current",
    response_model=CurrentStats,
    summary="Get current statistics",
    description="Retrieve current session statistics and performance metrics"
)
@limiter.limit(get_rate_limit_for_endpoint("stats"))
async def get_current_stats() -> CurrentStats:
    """
    Get current session statistics

    Returns aggregated stats including:
    - Total gold and XP
    - Current level and rank
    - Event counts (calls, meetings, etc.)
    - Progress to next level

    Returns:
        CurrentStats with all performance metrics

    Raises:
        HTTPException: 500 if stats retrieval fails
    """
    try:
        db = DatabaseQueries()
        stats = db.get_current_stats()

        return CurrentStats(
            total_gold=stats.get('total_gold', 0),
            total_xp=stats.get('total_xp', 0),
            current_level=stats.get('current_level', 1),
            xp_in_current_level=stats.get('xp_in_current_level', 0),
            xp_to_next_level=stats.get('xp_to_next_level', 1000),
            events_today=stats.get('events_today', 0),
            total_events=stats.get('total_events', 0),
            rank=stats.get('rank', 'Iron'),
            calls_made=stats.get('calls_made', 0),
            calls_connected=stats.get('calls_connected', 0),
            meetings_booked=stats.get('meetings_booked', 0)
        )

    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )
