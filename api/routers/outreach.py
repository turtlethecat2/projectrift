"""
Outreach sync endpoints.
Provides manual sync trigger and status reporting.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

import api.outreach_client as outreach_client
from api.scheduler import get_next_run_time
from api.config import settings
from api.schemas import OutreachStatus, OutreachSyncResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])


@router.post(
    "/sync",
    response_model=OutreachSyncResult,
    summary="Manually trigger Outreach activity sync",
)
async def manual_sync():
    """
    Immediately fetch new activity from Outreach and ingest it into Project Rift.
    Returns 401 if OAuth is not set up — visit /auth/outreach/start first.
    """
    if not outreach_client.is_authorized():
        raise HTTPException(
            status_code=401,
            detail="Not authorized with Outreach. Visit /auth/outreach/start to authenticate.",
        )
    count = outreach_client.run_sync()
    return OutreachSyncResult(
        status="success",
        events_ingested=count,
        synced_at=datetime.now(timezone.utc),
        message=f"Ingested {count} new events from Outreach",
    )


@router.get(
    "/status",
    response_model=OutreachStatus,
    summary="Get Outreach integration status",
)
async def sync_status():
    """
    Returns current OAuth authorization state, last sync time,
    token expiry, and next scheduled poll run.
    """
    tokens = outreach_client.load_tokens()
    return OutreachStatus(
        authorized=tokens is not None,
        last_synced_at=outreach_client.get_last_synced_at(),
        token_expires_at=tokens["expires_at"] if tokens else None,
        next_scheduled_run=get_next_run_time(),
        poll_interval_minutes=settings.OUTREACH_POLL_INTERVAL_MINUTES,
    )
