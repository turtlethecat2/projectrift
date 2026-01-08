"""
Pydantic schemas for request/response validation
Ensures type safety and data validation for API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime


class EventPayload(BaseModel):
    """Schema for incoming webhook events"""

    source: str = Field(
        ...,
        description="Source of the event",
        pattern="^(outreach|nooks|manual|zapier)$"
    )
    event_type: str = Field(
        ...,
        description="Type of sales event",
        min_length=1,
        max_length=50
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional event metadata"
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Event timestamp (defaults to now if not provided)"
    )

    @validator('event_type')
    def validate_event_type(cls, v):
        """Ensure event type is one of the allowed values"""
        allowed_types = [
            'call_dial',
            'call_connect',
            'meeting_booked',
            'meeting_attended',
            'email_sent'
        ]
        if v not in allowed_types:
            raise ValueError(
                f'Unknown event type: {v}. Allowed types: {", ".join(allowed_types)}'
            )
        return v

    @validator('metadata')
    def validate_metadata_size(cls, v):
        """Limit metadata size to prevent abuse"""
        if len(str(v)) > 5000:
            raise ValueError('Metadata too large (max 5000 characters)')
        return v

    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "source": "nooks",
                "event_type": "call_connect",
                "metadata": {
                    "prospect_name": "John Doe",
                    "company": "Acme Corp",
                    "call_duration": 180
                }
            }
        }


class EventResponse(BaseModel):
    """Schema for successful event creation response"""

    status: str = Field(default="success", description="Response status")
    event_id: str = Field(..., description="UUID of created event")
    gold_earned: int = Field(..., description="Gold awarded for this event")
    xp_earned: int = Field(..., description="XP awarded for this event")
    message: str = Field(default="Event processed successfully")
    duplicate: bool = Field(default=False, description="Whether this was a duplicate event")

    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "status": "success",
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "gold_earned": 100,
                "xp_earned": 40,
                "message": "Event processed successfully",
                "duplicate": False
            }
        }


class HealthResponse(BaseModel):
    """Schema for health check response"""

    status: str = Field(..., description="Overall system health status")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="Current server time")
    version: str = Field(..., description="API version")

    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "status": "healthy",
                "database": "connected",
                "timestamp": "2026-01-04T12:00:00Z",
                "version": "1.0.0"
            }
        }


class CurrentStats(BaseModel):
    """Schema for current session statistics"""

    total_gold: int = Field(..., description="Total gold earned")
    total_xp: int = Field(..., description="Total XP earned")
    current_level: int = Field(..., description="Current player level")
    xp_in_current_level: int = Field(..., description="XP progress in current level")
    xp_to_next_level: int = Field(..., description="XP needed for next level")
    events_today: int = Field(..., description="Number of events today")
    total_events: int = Field(..., description="Total number of events")
    rank: str = Field(..., description="Current rank (Iron to Challenger)")
    calls_made: int = Field(default=0, description="Total calls made")
    calls_connected: int = Field(default=0, description="Total calls connected")
    meetings_booked: int = Field(default=0, description="Total meetings booked")

    class Config:
        """Pydantic configuration"""
        schema_extra = {
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
                "meetings_booked": 1
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error responses"""

    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "detail": "Invalid webhook secret",
                "error_code": "UNAUTHORIZED",
                "timestamp": "2026-01-04T12:00:00Z"
            }
        }
