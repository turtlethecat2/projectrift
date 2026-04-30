"""Webhook ingestion endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from api.schemas import EventPayload, EventResponse
from api.security import get_rate_limit_for_endpoint, limiter, verify_webhook_secret
from database.queries import DatabaseQueries

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/webhook",
    tags=["webhooks"],
    responses={
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limited"},
    },
)


@router.post(
    "/ingest",
    response_model=EventResponse,
    status_code=201,
    summary="Ingest sales event",
)
@limiter.limit(get_rate_limit_for_endpoint("webhook"))
async def ingest_event(
    request: Request,
    payload: EventPayload,
    _: None = Depends(verify_webhook_secret),
) -> EventResponse:
    _ = request
    db = DatabaseQueries()

    if db.check_duplicate_event(
        source=payload.source,
        event_type=payload.event_type,
        metadata=payload.metadata or {},
        minutes=5,
    ):
        logger.info(
            "Duplicate event ignored: %s from %s", payload.event_type, payload.source
        )
        return EventResponse(
            status="success",
            event_id="duplicate",
            gold_earned=0,
            xp_earned=0,
            message="Duplicate event ignored (idempotency check)",
            duplicate=True,
        )

    rule = db.get_gamification_rule(payload.event_type)
    if rule is None:
        raise HTTPException(
            status_code=422,
            detail=f"No gamification rule configured for event type: {payload.event_type}",
        )

    gold_value = rule["gold_value"]
    xp_value = rule["xp_value"]
    event_id = db.insert_event(
        source=payload.source,
        event_type=payload.event_type,
        gold_value=gold_value,
        xp_value=xp_value,
        metadata=payload.metadata,
    )

    logger.info(
        "Event processed: %s | type=%s gold=%s xp=%s",
        event_id,
        payload.event_type,
        gold_value,
        xp_value,
    )

    return EventResponse(
        status="success",
        event_id=event_id,
        gold_earned=gold_value,
        xp_earned=xp_value,
        message="Event processed successfully",
        duplicate=False,
    )
