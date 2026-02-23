"""
Outreach API client for Project Rift.
Handles OAuth token management, activity fetching, and event mapping.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from api.config import settings

logger = logging.getLogger(__name__)

# ── Outreach API field names ──────────────────────────────────────────────────
# If Outreach renames these fields in their API, update the constants here.
# Docs: https://api.outreach.io/api/v2/docs

OUTREACH_BASE_URL = "https://api.outreach.io"
OUTREACH_TOKEN_URL = "https://api.outreach.io/oauth/token"
OUTREACH_AUTH_URL = "https://api.outreach.io/oauth/authorize"
OUTREACH_SCOPES = "calls.read meetings.read"

# Outreach call resource (GET /api/v2/calls)
CALL_ANSWERED_FIELD = "answeredAt"   # null = unanswered; timestamp string = connected
CALL_CREATED_FIELD = "createdAt"    # when the call record was created

# Outreach meeting resource (GET /api/v2/meetings)
MEETING_CREATED_FIELD = "createdAt"  # when the meeting was booked

# ── In-memory token cache ─────────────────────────────────────────────────────
# Caches tokens for one poll cycle to avoid repeated DB reads.
# Invalidated after every refresh.
_token_cache: Optional[Dict[str, Any]] = None


def _invalidate_cache() -> None:
    global _token_cache
    _token_cache = None


# ── Token persistence ─────────────────────────────────────────────────────────

def save_tokens(access_token: str, refresh_token: str, expires_at: datetime) -> None:
    """Upsert tokens to DB and update the in-memory cache."""
    global _token_cache
    from database.queries import DatabaseQueries
    db = DatabaseQueries()
    db.save_oauth_tokens("outreach", access_token, refresh_token, expires_at)
    _token_cache = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
    }


def load_tokens() -> Optional[Dict[str, Any]]:
    """Load tokens from in-memory cache, falling back to DB."""
    global _token_cache
    if _token_cache is not None:
        return _token_cache
    from database.queries import DatabaseQueries
    db = DatabaseQueries()
    row = db.load_oauth_tokens("outreach")
    if row is None:
        return None
    _token_cache = dict(row)
    return _token_cache


def is_authorized() -> bool:
    """Return True if OAuth tokens exist in DB."""
    return load_tokens() is not None


# ── Token refresh ─────────────────────────────────────────────────────────────

def needs_refresh(tokens: Dict[str, Any], buffer_minutes: int = 10) -> bool:
    """Return True if the access token expires within buffer_minutes."""
    expires_at = tokens["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc) + timedelta(minutes=buffer_minutes)


def refresh_tokens() -> Optional[Dict[str, Any]]:
    """Exchange refresh token for a new access token. Returns updated tokens or None on failure."""
    tokens = load_tokens()
    if tokens is None:
        logger.error("Cannot refresh: no tokens stored")
        return None
    try:
        response = httpx.post(
            OUTREACH_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": tokens["refresh_token"],
                "client_id": settings.OUTREACH_CLIENT_ID,
                "client_secret": settings.OUTREACH_CLIENT_SECRET,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
        save_tokens(data["access_token"], data["refresh_token"], expires_at)
        logger.info("Outreach tokens refreshed successfully")
        return load_tokens()
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        _invalidate_cache()
        return None


def get_valid_access_token() -> Optional[str]:
    """Return a valid access token, refreshing if needed. Returns None if unauthorized."""
    tokens = load_tokens()
    if tokens is None:
        return None
    if needs_refresh(tokens):
        tokens = refresh_tokens()
        if tokens is None:
            return None
    return tokens["access_token"]


# ── Sync state ────────────────────────────────────────────────────────────────

def update_last_synced_at(synced_at: datetime) -> None:
    """Update the polling high-water mark in the DB."""
    from database.queries import DatabaseQueries
    db = DatabaseQueries()
    db.update_last_synced_at("outreach", synced_at)


def get_last_synced_at() -> Optional[datetime]:
    """Return the timestamp of the last successful sync, or None."""
    from database.queries import DatabaseQueries
    db = DatabaseQueries()
    return db.get_last_synced_at("outreach")


# ── Activity fetching ─────────────────────────────────────────────────────────

def _fetch_calls(access_token: str, since: Optional[datetime]) -> List[dict]:
    """
    Fetch call records from Outreach API created after `since`.
    Returns raw list of Outreach call data objects, or [] on error.
    """
    params: Dict[str, Any] = {"sort": CALL_CREATED_FIELD, "page[size]": 100}
    if since:
        params[f"filter[{CALL_CREATED_FIELD}][gte]"] = since.isoformat()
    try:
        response = httpx.get(
            f"{OUTREACH_BASE_URL}/api/v2/calls",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch calls from Outreach: {e}")
        return []


def _fetch_meetings(access_token: str, since: Optional[datetime]) -> List[dict]:
    """
    Fetch meeting records from Outreach API created after `since`.
    Returns raw list of Outreach meeting data objects, or [] on error.
    """
    params: Dict[str, Any] = {"sort": MEETING_CREATED_FIELD, "page[size]": 100}
    if since:
        params[f"filter[{MEETING_CREATED_FIELD}][gte]"] = since.isoformat()
    try:
        response = httpx.get(
            f"{OUTREACH_BASE_URL}/api/v2/meetings",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch meetings from Outreach: {e}")
        return []


# ── Activity mapping ──────────────────────────────────────────────────────────

def map_calls_to_events(calls: List[dict]) -> List[Dict[str, Any]]:
    """
    Map Outreach call records to Project Rift event dicts.

    Outreach fields used (update CALL_* constants above if these change):
      attributes.createdAt  → timestamp
      attributes.answeredAt → null means no connect; any value means connected
    """
    events = []
    for call in calls:
        attrs = call.get("attributes", {})
        metadata = {"outreach_call_id": call.get("id")}
        timestamp = attrs.get(CALL_CREATED_FIELD)

        # Every call attempt = call_dial
        events.append({
            "source": "outreach",
            "event_type": "call_dial",
            "metadata": metadata,
            "timestamp": timestamp,
        })

        # Answered call = also call_connect (answeredAt is non-null)
        if attrs.get(CALL_ANSWERED_FIELD) is not None:
            events.append({
                "source": "outreach",
                "event_type": "call_connect",
                "metadata": metadata,
                "timestamp": timestamp,
            })
    return events


def map_meetings_to_events(meetings: List[dict]) -> List[Dict[str, Any]]:
    """
    Map Outreach meeting records to Project Rift event dicts.

    Outreach fields used (update MEETING_* constants above if these change):
      attributes.createdAt → when the meeting was booked
    """
    events = []
    for meeting in meetings:
        attrs = meeting.get("attributes", {})
        events.append({
            "source": "outreach",
            "event_type": "meeting_booked",
            "metadata": {"outreach_meeting_id": meeting.get("id")},
            "timestamp": attrs.get(MEETING_CREATED_FIELD),
        })
    return events


# ── Ingestion ─────────────────────────────────────────────────────────────────

def _ingest_events(event_dicts: List[Dict[str, Any]]) -> int:
    """
    Submit mapped events directly to the database (bypasses HTTP).
    Returns count of non-duplicate events successfully ingested.
    """
    from database.queries import DatabaseQueries
    from api.schemas import EventPayload
    db = DatabaseQueries()
    count = 0
    for event_dict in event_dicts:
        try:
            payload = EventPayload(**event_dict)
        except Exception as e:
            logger.warning(f"Skipping invalid event dict: {e}")
            continue
        if db.check_duplicate_event(
            source=payload.source,
            event_type=payload.event_type,
            metadata=payload.metadata or {},
            minutes=5,
        ):
            continue
        rule = db.get_gamification_rule(payload.event_type)
        if rule is None:
            logger.warning(f"No gamification rule for {payload.event_type}, skipping")
            continue
        db.insert_event(
            source=payload.source,
            event_type=payload.event_type,
            gold_value=rule["gold_value"],
            xp_value=rule["xp_value"],
            metadata=payload.metadata or {},
        )
        count += 1
    return count


# ── Sync entry point ──────────────────────────────────────────────────────────

def run_sync() -> int:
    """
    Fetch new Outreach activity and ingest into Project Rift.
    Returns count of events ingested. Safe to call at any time.
    """
    access_token = get_valid_access_token()
    if access_token is None:
        logger.error("Sync skipped: no valid Outreach access token")
        return 0

    since = get_last_synced_at()
    sync_start = datetime.now(timezone.utc)

    calls = _fetch_calls(access_token, since)
    meetings = _fetch_meetings(access_token, since)

    events = map_calls_to_events(calls) + map_meetings_to_events(meetings)
    count = _ingest_events(events)

    update_last_synced_at(sync_start)
    logger.info(f"Outreach sync complete: {count} new events ingested")
    return count
