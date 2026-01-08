"""
Webhook endpoints for event ingestion
Handles incoming sales activity events from external sources
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from api.schemas import EventPayload, EventResponse
from api.security import verify_webhook_secret, limiter, get_rate_limit_for_endpoint
from api.database import get_db_pool
from database.queries import DatabaseQueries

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/webhook",
    tags=["webhooks"],
    responses={
        401: {"description": "Unauthorized - Invalid webhook secret"},
        422: {"description": "Validation Error - Invalid payload"},
        429: {"description": "Too Many Requests - Rate limit exceeded"}
    }
)


@router.post(
    "/ingest",
    response_model=EventResponse,
    status_code=201,
    summary="Ingest sales event",
    description="Receive and process sales activity events from external sources"
)
@limiter.limit(get_rate_limit_for_endpoint("webhook"))
async def ingest_event(
    payload: EventPayload,
    _: None = Depends(verify_webhook_secret)
) -> EventResponse:
    """
    Universal endpoint for webhook data ingestion

    This endpoint:
    1. Validates the webhook secret
    2. Validates the payload schema
    3. Checks for duplicate events
    4. Looks up gold/XP values from gamification rules
    5. Stores the event in the database
    6. Returns confirmation with rewards

    Args:
        payload: Event data (source, event_type, metadata)
        _: Webhook secret verification (dependency)

    Returns:
        EventResponse with event_id and reward amounts

    Raises:
        HTTPException: 401 if secret invalid, 422 if payload invalid
    """
    try:
        db = DatabaseQueries()

        # Check for duplicate events (idempotency)
        is_duplicate = db.check_duplicate_event(
            source=payload.source,
            event_type=payload.event_type,
            metadata=payload.metadata,
            minutes=5
        )

        if is_duplicate:
            logger.info(
                f"Duplicate event detected: {payload.event_type} from {payload.source}"
            )
            # Return success but indicate it's a duplicate
            return EventResponse(
                status="success",
                event_id="duplicate",
                gold_earned=0,
                xp_earned=0,
                message="Duplicate event ignored (idempotency check)",
                duplicate=True
            )

        # Get gamification rules for this event type
        rule = db.get_gamification_rule(payload.event_type)

        if rule is None:
            logger.error(f"No gamification rule found for event type: {payload.event_type}")
            raise HTTPException(
                status_code=422,
                detail=f"No gamification rule configured for event type: {payload.event_type}"
            )

        gold_value = rule['gold_value']
        xp_value = rule['xp_value']

        # Insert the event
        event_id = db.insert_event(
            source=payload.source,
            event_type=payload.event_type,
            gold_value=gold_value,
            xp_value=xp_value,
            metadata=payload.metadata
        )

        logger.info(
            f"Event processed: {event_id} | Type: {payload.event_type} | "
            f"Gold: {gold_value} | XP: {xp_value}"
        )

        return EventResponse(
            status="success",
            event_id=event_id,
            gold_earned=gold_value,
            xp_earned=xp_value,
            message="Event processed successfully",
            duplicate=False
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while processing event: {str(e)}"
        )
