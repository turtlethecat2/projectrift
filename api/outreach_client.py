"""Outreach OAuth + activity sync (optional integration)."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from api.config import settings

logger = logging.getLogger(__name__)

OUTREACH_BASE_URL = "https://api.outreach.io"
OUTREACH_TOKEN_URL = "https://api.outreach.io/oauth/token"
OUTREACH_AUTH_URL = "https://api.outreach.io/oauth/authorize"
OUTREACH_SCOPES = "calls.read"

CALL_ANSWERED_FIELD = "answeredAt"
CALL_CREATED_FIELD = "createdAt"
MEETING_CREATED_FIELD = "createdAt"

_token_cache: Optional[Dict[str, Any]] = None


def _invalidate_cache() -> None:
    global _token_cache
    _token_cache = None


def save_tokens(access_token: str, refresh_token: str, expires_at: datetime) -> None:
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
    return load_tokens() is not None


def needs_refresh(tokens: Dict[str, Any], buffer_minutes: int = 10) -> bool:
    expires_at = tokens["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc) + timedelta(minutes=buffer_minutes)


def refresh_tokens() -> Optional[Dict[str, Any]]:
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
            },
            auth=(settings.OUTREACH_CLIENT_ID, settings.OUTREACH_CLIENT_SECRET),
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
        save_tokens(data["access_token"], data["refresh_token"], expires_at)
        logger.info("Outreach tokens refreshed successfully")
        return load_tokens()
    except Exception as e:
        logger.error("Token refresh failed: %s", e)
        _invalidate_cache()
        return None


def get_valid_access_token() -> Optional[str]:
    tokens = load_tokens()
    if tokens is None:
        return None
    if needs_refresh(tokens):
        tokens = refresh_tokens()
        if tokens is None:
            return None
    return tokens["access_token"]


def update_last_synced_at(synced_at: datetime) -> None:
    from database.queries import DatabaseQueries

    db = DatabaseQueries()
    db.update_last_synced_at("outreach", synced_at)


def get_last_synced_at() -> Optional[datetime]:
    from database.queries import DatabaseQueries

    db = DatabaseQueries()
    return db.get_last_synced_at("outreach")


def _fetch_calls(access_token: str, since: Optional[datetime]) -> List[dict]:
    params: Dict[str, Any] = {"sort": CALL_CREATED_FIELD, "page[size]": 100}
    if since:
        since_str = since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        params[f"filter[{CALL_CREATED_FIELD}]"] = f"{since_str}..inf"
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
        logger.error("Failed to fetch calls from Outreach: %s", e)
        return []


def _fetch_meetings(access_token: str, since: Optional[datetime]) -> List[dict]:
    params: Dict[str, Any] = {"sort": MEETING_CREATED_FIELD, "page[size]": 100}
    if since:
        since_str = since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        params[f"filter[{MEETING_CREATED_FIELD}]"] = f"{since_str}..inf"
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
        logger.error("Failed to fetch meetings from Outreach: %s", e)
        return []


def map_calls_to_events(calls: List[dict]) -> List[Dict[str, Any]]:
    events = []
    for call in calls:
        attrs = call.get("attributes", {})
        metadata = {"outreach_call_id": call.get("id")}
        timestamp = attrs.get(CALL_CREATED_FIELD)

        events.append(
            {
                "source": "outreach",
                "event_type": "call_dial",
                "metadata": metadata,
                "timestamp": timestamp,
            }
        )

        if attrs.get(CALL_ANSWERED_FIELD) is not None:
            events.append(
                {
                    "source": "outreach",
                    "event_type": "call_connect",
                    "metadata": metadata,
                    "timestamp": timestamp,
                }
            )
    return events


def map_meetings_to_events(meetings: List[dict]) -> List[Dict[str, Any]]:
    events = []
    for meeting in meetings:
        attrs = meeting.get("attributes", {})
        events.append(
            {
                "source": "outreach",
                "event_type": "meeting_booked",
                "metadata": {"outreach_meeting_id": meeting.get("id")},
                "timestamp": attrs.get(MEETING_CREATED_FIELD),
            }
        )
    return events


def _ingest_events(event_dicts: List[Dict[str, Any]]) -> int:
    from api.schemas import EventPayload
    from database.queries import DatabaseQueries

    db = DatabaseQueries()
    count = 0
    for event_dict in event_dicts:
        try:
            payload = EventPayload(**event_dict)
        except Exception as e:
            logger.warning("Skipping invalid event dict: %s", e)
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
            logger.warning("No gamification rule for %s, skipping", payload.event_type)
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


def run_sync() -> int:
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
    logger.info("Outreach sync complete: %s new events ingested", count)
    return count
