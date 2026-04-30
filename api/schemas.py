"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventPayload(BaseModel):
    source: str = Field(
        ...,
        description="Source of the event",
        pattern="^(outreach|nooks|manual|zapier)$",
    )
    event_type: str = Field(
        ..., description="Type of sales event", min_length=1, max_length=50
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional event metadata"
    )
    timestamp: Optional[datetime] = Field(
        default=None, description="Event timestamp (defaults to now if not provided)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "nooks",
                "event_type": "call_connect",
                "metadata": {
                    "prospect_name": "John Doe",
                    "company": "Acme Corp",
                    "call_duration": 180,
                },
            }
        }
    )

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        allowed_types = [
            "call_dial",
            "call_connect",
            "meeting_booked",
            "meeting_attended",
            "email_sent",
        ]
        if v not in allowed_types:
            raise ValueError(
                f"Unknown event type: {v}. Allowed: {', '.join(allowed_types)}"
            )
        return v

    @field_validator("metadata")
    @classmethod
    def validate_metadata_size(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is not None and len(str(v)) > 5000:
            raise ValueError("Metadata too large (max 5000 characters)")
        return v


class EventResponse(BaseModel):
    status: str = Field(default="success", description="Response status")
    event_id: str = Field(..., description="UUID of created event")
    gold_earned: int = Field(..., description="Gold awarded for this event")
    xp_earned: int = Field(..., description="XP awarded for this event")
    message: str = Field(default="Event processed successfully")
    duplicate: bool = Field(
        default=False, description="Whether this was a duplicate event"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "gold_earned": 100,
                "xp_earned": 40,
                "message": "Event processed successfully",
                "duplicate": False,
            }
        }
    )


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
    version: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "database": "connected",
                "timestamp": "2026-01-04T12:00:00Z",
                "version": "1.0.0",
            }
        }
    )


class CurrentStats(BaseModel):
    total_gold: int
    total_xp: int
    current_level: int
    xp_in_current_level: int
    xp_to_next_level: int
    events_today: int
    total_events: int
    rank: str
    calls_made: int = 0
    calls_connected: int = 0
    meetings_booked: int = 0

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_gold": 2450,
                "total_xp": 1200,
                "current_level": 2,
                "xp_in_current_level": 200,
                "xp_to_next_level": 800,
                "events_today": 42,
                "total_events": 156,
                "rank": "Gold",
                "calls_made": 12,
                "calls_connected": 4,
                "meetings_booked": 1,
            }
        }
    )


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Invalid webhook secret",
                "error_code": "UNAUTHORIZED",
            }
        }
    )


class OutreachAuthStatus(BaseModel):
    status: str
    expires_at: Optional[datetime] = None
    message: str


class OutreachSyncResult(BaseModel):
    status: str = "success"
    events_ingested: int
    synced_at: datetime
    message: str


class OutreachStatus(BaseModel):
    authorized: bool
    last_synced_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None
    next_scheduled_run: Optional[datetime] = None
    poll_interval_minutes: int
