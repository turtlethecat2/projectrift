"""Outreach manual sync + status (optional)."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

import api.outreach_client as outreach_client
from api.config import settings
from api.scheduler import get_next_run_time
from api.schemas import OutreachStatus, OutreachSyncResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])


@router.post("/sync", response_model=OutreachSyncResult, summary="Run Outreach sync now")
async def manual_sync():
    if not outreach_client.is_authorized():
        raise HTTPException(
            status_code=401,
            detail="Not authorized with Outreach. Visit /auth/outreach/start first.",
        )
    count = outreach_client.run_sync()
    return OutreachSyncResult(
        status="success",
        events_ingested=count,
        synced_at=datetime.now(timezone.utc),
        message=f"Ingested {count} new events from Outreach",
    )


@router.get("/status", response_model=OutreachStatus, summary="Outreach integration status")
async def sync_status():
    tokens = outreach_client.load_tokens()
    return OutreachStatus(
        authorized=tokens is not None,
        last_synced_at=outreach_client.get_last_synced_at(),
        token_expires_at=tokens["expires_at"] if tokens else None,
        next_scheduled_run=get_next_run_time(),
        poll_interval_minutes=settings.OUTREACH_POLL_INTERVAL_MINUTES,
    )
