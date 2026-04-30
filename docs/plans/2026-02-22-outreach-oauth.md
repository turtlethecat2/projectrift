# Outreach OAuth Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add full Outreach OAuth 2.0 integration — auth flow, token storage in PostgreSQL, scheduled activity polling (weekdays CT business hours), and a manual sync endpoint.

**Architecture:** New `api/outreach_client.py` handles all Outreach API calls and token management. New `api/scheduler.py` runs APScheduler inside the FastAPI process. New routers (`auth`, `outreach`) expose the OAuth callback and sync endpoints.

**Tech Stack:** FastAPI · httpx (already in requirements) · APScheduler 3.x · psycopg2 · PostgreSQL

---

### Task 1: Install APScheduler and add to requirements

**Files:**
- Modify: `requirements.txt`

**Step 1: Add apscheduler to requirements.txt**

In `requirements.txt`, add under `# API Features`:

```
apscheduler>=3.10.0,<4.0
```

**Step 2: Install it**

```bash
pip install "apscheduler>=3.10.0,<4.0"
```

Expected: `Successfully installed apscheduler-3.x.x`

**Step 3: Verify install**

```bash
python -c "from apscheduler.schedulers.asyncio import AsyncIOScheduler; print('ok')"
```

Expected: `ok`

**Step 4: Commit**

```bash
git add requirements.txt
git commit -m "feat: add apscheduler dependency for Outreach polling"
```

---

### Task 2: Database migration — oauth_tokens table

**Files:**
- Create: `database/oauth_tokens.sql`

**Step 1: Write the failing test**

In `tests/test_api.py`, add to the bottom:

```python
class TestOAuthTokensTable:
    """Verify oauth_tokens table exists and has correct structure"""

    def test_oauth_tokens_table_exists(self):
        """oauth_tokens table must exist after migration"""
        from database.queries import DatabaseQueries
        db = DatabaseQueries()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'oauth_tokens'
            ORDER BY column_name
        """)
        columns = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        assert "access_token" in columns
        assert "refresh_token" in columns
        assert "expires_at" in columns
        assert "last_synced_at" in columns
        assert "provider" in columns
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py::TestOAuthTokensTable::test_oauth_tokens_table_exists -v
```

Expected: FAIL — table does not exist yet

**Step 3: Create the migration SQL**

Create `database/oauth_tokens.sql`:

```sql
-- Migration: Add oauth_tokens table for Outreach OAuth integration
-- Run: psql $DATABASE_URL -f database/oauth_tokens.sql

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id             SERIAL PRIMARY KEY,
    provider       VARCHAR(50) NOT NULL UNIQUE DEFAULT 'outreach',
    access_token   TEXT NOT NULL,
    refresh_token  TEXT NOT NULL,
    expires_at     TIMESTAMPTZ NOT NULL,
    last_synced_at TIMESTAMPTZ,
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);
```

**Step 4: Run the migration**

```bash
psql $DATABASE_URL -f database/oauth_tokens.sql
```

Expected: `CREATE TABLE`

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_api.py::TestOAuthTokensTable::test_oauth_tokens_table_exists -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add database/oauth_tokens.sql tests/test_api.py
git commit -m "feat: add oauth_tokens table migration"
```

---

### Task 3: Add OAuth token methods to DatabaseQueries

**Files:**
- Modify: `database/queries.py`

**Step 1: Write the failing tests**

Add to `tests/test_api.py` inside `TestOAuthTokensTable`:

```python
    def test_save_and_load_tokens(self):
        """save_oauth_tokens upserts and load_oauth_tokens retrieves"""
        from database.queries import DatabaseQueries
        from datetime import datetime, timezone, timedelta
        db = DatabaseQueries()
        expires = datetime.now(timezone.utc) + timedelta(hours=2)
        db.save_oauth_tokens("outreach", "acc_test", "ref_test", expires)
        tokens = db.load_oauth_tokens("outreach")
        assert tokens is not None
        assert tokens["access_token"] == "acc_test"
        assert tokens["refresh_token"] == "ref_test"

    def test_update_last_synced_at(self):
        """update_last_synced_at sets the high-water mark"""
        from database.queries import DatabaseQueries
        from datetime import datetime, timezone
        db = DatabaseQueries()
        now = datetime.now(timezone.utc)
        db.update_last_synced_at("outreach", now)
        result = db.get_last_synced_at("outreach")
        assert result is not None
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py::TestOAuthTokensTable -v
```

Expected: FAIL — methods don't exist yet

**Step 3: Add methods to DatabaseQueries**

In `database/queries.py`, add these four methods to the `DatabaseQueries` class (after `check_duplicate_event`):

```python
    def save_oauth_tokens(
        self,
        provider: str,
        access_token: str,
        refresh_token: str,
        expires_at: "datetime",
    ) -> None:
        """
        Upsert OAuth tokens for a provider into oauth_tokens table.

        Args:
            provider: OAuth provider name (e.g. 'outreach')
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_at: Token expiry datetime (timezone-aware)
        """
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO oauth_tokens (provider, access_token, refresh_token, expires_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (provider) DO UPDATE SET
                    access_token  = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at    = EXCLUDED.expires_at,
                    updated_at    = NOW()
                """,
                (provider, access_token, refresh_token, expires_at),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def load_oauth_tokens(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        Load OAuth tokens for a provider from oauth_tokens table.

        Args:
            provider: OAuth provider name (e.g. 'outreach')

        Returns:
            Dict with access_token, refresh_token, expires_at — or None if not found
        """
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(
                "SELECT access_token, refresh_token, expires_at FROM oauth_tokens WHERE provider = %s",
                (provider,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            cur.close()
            conn.close()

    def update_last_synced_at(self, provider: str, synced_at: "datetime") -> None:
        """
        Update the last_synced_at high-water mark for a provider.

        Args:
            provider: OAuth provider name (e.g. 'outreach')
            synced_at: Timestamp of the successful sync
        """
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE oauth_tokens SET last_synced_at = %s WHERE provider = %s",
                (synced_at, provider),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def get_last_synced_at(self, provider: str) -> Optional["datetime"]:
        """
        Get the last_synced_at high-water mark for a provider.

        Args:
            provider: OAuth provider name (e.g. 'outreach')

        Returns:
            datetime of last sync, or None if never synced
        """
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(
                "SELECT last_synced_at FROM oauth_tokens WHERE provider = %s",
                (provider,),
            )
            row = cur.fetchone()
            return row["last_synced_at"] if row else None
        finally:
            cur.close()
            conn.close()
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py::TestOAuthTokensTable -v
```

Expected: all 3 PASS

**Step 5: Commit**

```bash
git add database/queries.py tests/test_api.py
git commit -m "feat: add OAuth token CRUD methods to DatabaseQueries"
```

---

### Task 4: Add Outreach OAuth settings to config

**Files:**
- Modify: `api/config.py`

**Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
class TestOutreachConfig:
    """Verify Outreach OAuth config fields exist"""

    def test_outreach_config_fields_exist(self):
        """Settings must have Outreach OAuth fields"""
        from api.config import settings
        assert hasattr(settings, "OUTREACH_CLIENT_ID")
        assert hasattr(settings, "OUTREACH_CLIENT_SECRET")
        assert hasattr(settings, "OUTREACH_REDIRECT_URI")
        assert hasattr(settings, "OUTREACH_POLL_INTERVAL_MINUTES")
        assert settings.OUTREACH_POLL_INTERVAL_MINUTES == 15  # default
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py::TestOutreachConfig -v
```

Expected: FAIL — fields don't exist yet

**Step 3: Add fields to Settings**

In `api/config.py`, add these fields to the `Settings` class after `NOOKS_API_KEY`:

```python
    # Outreach OAuth
    OUTREACH_CLIENT_ID: Optional[str] = None
    OUTREACH_CLIENT_SECRET: Optional[str] = None
    OUTREACH_REDIRECT_URI: Optional[str] = None
    OUTREACH_POLL_INTERVAL_MINUTES: int = 15
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_api.py::TestOutreachConfig -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add api/config.py tests/test_api.py
git commit -m "feat: add Outreach OAuth settings to config"
```

---

### Task 5: Add OAuth/sync schemas

**Files:**
- Modify: `api/schemas.py`

**Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
class TestOutreachSchemas:
    """Verify Outreach OAuth/sync Pydantic schemas"""

    def test_outreach_auth_status_schema(self):
        from api.schemas import OutreachAuthStatus
        s = OutreachAuthStatus(status="authorized", message="ok")
        assert s.status == "authorized"

    def test_outreach_sync_result_schema(self):
        from api.schemas import OutreachSyncResult
        from datetime import datetime, timezone
        s = OutreachSyncResult(
            status="success",
            events_ingested=5,
            synced_at=datetime.now(timezone.utc),
            message="ok",
        )
        assert s.events_ingested == 5

    def test_outreach_status_schema(self):
        from api.schemas import OutreachStatus
        s = OutreachStatus(
            authorized=True,
            last_synced_at=None,
            token_expires_at=None,
            next_scheduled_run=None,
            poll_interval_minutes=15,
        )
        assert s.authorized is True
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py::TestOutreachSchemas -v
```

Expected: FAIL — schemas not defined yet

**Step 3: Add schemas to api/schemas.py**

Add at the bottom of `api/schemas.py`:

```python
class OutreachAuthStatus(BaseModel):
    """Response for OAuth authorization endpoints"""

    status: str = Field(..., description="authorized or error")
    expires_at: Optional[datetime] = Field(None, description="Token expiry time")
    message: str = Field(..., description="Human-readable status message")


class OutreachSyncResult(BaseModel):
    """Response for manual sync endpoint"""

    status: str = Field(default="success")
    events_ingested: int = Field(..., description="Number of new events ingested")
    synced_at: datetime = Field(..., description="Timestamp of this sync run")
    message: str = Field(..., description="Human-readable result message")


class OutreachStatus(BaseModel):
    """Response for sync status endpoint"""

    authorized: bool = Field(..., description="Whether OAuth is set up")
    last_synced_at: Optional[datetime] = Field(None, description="Last successful sync")
    token_expires_at: Optional[datetime] = Field(None, description="When access token expires")
    next_scheduled_run: Optional[datetime] = Field(None, description="Next scheduled poll time")
    poll_interval_minutes: int = Field(..., description="Poll interval in minutes")
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py::TestOutreachSchemas -v
```

Expected: all 3 PASS

**Step 5: Commit**

```bash
git add api/schemas.py tests/test_api.py
git commit -m "feat: add Outreach OAuth/sync Pydantic schemas"
```

---

### Task 6: Create outreach_client.py — token management

**Files:**
- Create: `api/outreach_client.py`

**Step 1: Write the failing tests**

Add to `tests/test_api.py`:

```python
class TestOutreachClient:
    """Unit tests for outreach_client token management"""

    def test_needs_refresh_when_expiring_soon(self):
        """needs_refresh returns True when token expires within buffer window"""
        from api.outreach_client import needs_refresh
        from datetime import datetime, timezone, timedelta
        tokens = {"expires_at": datetime.now(timezone.utc) + timedelta(minutes=5)}
        assert needs_refresh(tokens, buffer_minutes=10) is True

    def test_needs_refresh_when_not_expiring(self):
        """needs_refresh returns False when token has plenty of time left"""
        from api.outreach_client import needs_refresh
        from datetime import datetime, timezone, timedelta
        tokens = {"expires_at": datetime.now(timezone.utc) + timedelta(hours=1)}
        assert needs_refresh(tokens, buffer_minutes=10) is False

    def test_map_calls_to_events_unanswered(self):
        """Unanswered call produces only call_dial event"""
        from api.outreach_client import map_calls_to_events
        calls = [{"id": "c1", "attributes": {"answeredAt": None, "createdAt": "2026-02-22T10:00:00Z"}}]
        events = map_calls_to_events(calls)
        assert len(events) == 1
        assert events[0]["event_type"] == "call_dial"

    def test_map_calls_to_events_answered(self):
        """Answered call produces call_dial AND call_connect events"""
        from api.outreach_client import map_calls_to_events
        calls = [{"id": "c2", "attributes": {"answeredAt": "2026-02-22T10:01:00Z", "createdAt": "2026-02-22T10:00:00Z"}}]
        events = map_calls_to_events(calls)
        assert len(events) == 2
        types = {e["event_type"] for e in events}
        assert "call_dial" in types
        assert "call_connect" in types

    def test_map_meetings_to_events(self):
        """Meeting record produces meeting_booked event"""
        from api.outreach_client import map_meetings_to_events
        meetings = [{"id": "m1", "attributes": {"createdAt": "2026-02-22T14:00:00Z"}}]
        events = map_meetings_to_events(meetings)
        assert len(events) == 1
        assert events[0]["event_type"] == "meeting_booked"
        assert events[0]["source"] == "outreach"
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py::TestOutreachClient -v
```

Expected: FAIL — module doesn't exist yet

**Step 3: Create api/outreach_client.py**

```python
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
        # Outreach date filter: filter[createdAt][gte]=<ISO8601>
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


# ─�� Activity mapping ──────────────────────────────────────────────────────────

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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py::TestOutreachClient -v
```

Expected: all 5 PASS

**Step 5: Commit**

```bash
git add api/outreach_client.py tests/test_api.py
git commit -m "feat: add outreach_client with token management and activity mapping"
```

---

### Task 7: Create scheduler.py

**Files:**
- Create: `api/scheduler.py`

**Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
class TestScheduler:
    """Verify scheduler module exports expected functions"""

    def test_scheduler_imports(self):
        from api.scheduler import start_scheduler, stop_scheduler, get_next_run_time, scheduler
        assert callable(start_scheduler)
        assert callable(stop_scheduler)
        assert callable(get_next_run_time)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py::TestScheduler -v
```

Expected: FAIL — module doesn't exist

**Step 3: Create api/scheduler.py**

```python
"""
APScheduler setup for Outreach activity polling.
Runs poll job Mon-Fri 8am-5pm America/Chicago every OUTREACH_POLL_INTERVAL_MINUTES.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _poll_job() -> None:
    """Scheduled job: fetch Outreach activity and ingest into Project Rift."""
    from api.outreach_client import run_sync
    try:
        count = run_sync()
        logger.info(f"Scheduled Outreach sync complete: {count} events ingested")
    except Exception as e:
        logger.error(f"Scheduled Outreach sync failed: {e}", exc_info=True)


def start_scheduler() -> None:
    """Start the APScheduler. Called once during FastAPI lifespan startup."""
    scheduler.add_job(
        _poll_job,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour="8-17",
            minute=f"*/{settings.OUTREACH_POLL_INTERVAL_MINUTES}",
            timezone="America/Chicago",
        ),
        id="outreach_poll",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"Outreach scheduler started "
        f"(Mon-Fri 8am-5pm CT, every {settings.OUTREACH_POLL_INTERVAL_MINUTES} min)"
    )


def stop_scheduler() -> None:
    """Stop the scheduler. Called during FastAPI lifespan shutdown."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Outreach scheduler stopped")


def get_next_run_time():
    """Return the next scheduled run time, or None if scheduler isn't running."""
    job = scheduler.get_job("outreach_poll")
    return job.next_run_time if job else None
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_api.py::TestScheduler -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add api/scheduler.py tests/test_api.py
git commit -m "feat: add APScheduler for Outreach polling (Mon-Fri 8am-5pm CT)"
```

---

### Task 8: Create auth router

**Files:**
- Create: `api/routers/auth.py`

**Step 1: Write the failing tests**

Add to `tests/test_api.py`:

```python
class TestOutreachAuthRouter:
    """Tests for Outreach OAuth endpoints"""

    def test_start_redirects_to_outreach(self):
        """GET /auth/outreach/start redirects to Outreach authorization URL"""
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app, follow_redirects=False)
        response = client.get("/auth/outreach/start")
        assert response.status_code == 307
        assert "api.outreach.io/oauth/authorize" in response.headers["location"]

    def test_callback_rejects_error_param(self):
        """GET /auth/outreach/callback?error=... returns 400"""
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app)
        response = client.get("/auth/outreach/callback?error=access_denied")
        assert response.status_code == 400
        assert "access_denied" in response.json()["detail"]

    def test_callback_rejects_invalid_state(self):
        """GET /auth/outreach/callback with unknown state returns 400"""
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app)
        response = client.get("/auth/outreach/callback?code=abc&state=invalid_state")
        assert response.status_code == 400
        assert "state" in response.json()["detail"].lower()
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py::TestOutreachAuthRouter -v
```

Expected: FAIL — router not registered yet

**Step 3: Create api/routers/auth.py**

```python
"""
OAuth 2.0 endpoints for Outreach integration.
Handles the authorization redirect and token exchange callback.
"""

import logging
import secrets
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from api.config import settings
from api.outreach_client import (
    OUTREACH_AUTH_URL,
    OUTREACH_SCOPES,
    OUTREACH_TOKEN_URL,
    save_tokens,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# CSRF protection: pending state tokens (single-user, in-memory is sufficient)
_pending_states: set[str] = set()


@router.get("/outreach/start", summary="Start Outreach OAuth authorization flow")
async def outreach_start():
    """
    Redirect the user to Outreach's authorization page.
    Generates a CSRF state token to verify the callback.
    """
    state = secrets.token_urlsafe(32)
    _pending_states.add(state)

    params = {
        "client_id": settings.OUTREACH_CLIENT_ID,
        "redirect_uri": settings.OUTREACH_REDIRECT_URI,
        "response_type": "code",
        "scope": OUTREACH_SCOPES,
        "state": state,
    }
    auth_url = OUTREACH_AUTH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=auth_url)


@router.get("/outreach/callback", summary="Handle Outreach OAuth callback")
async def outreach_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
):
    """
    Receive the OAuth callback from Outreach.

    - If Outreach sends ?error=..., return 400 immediately.
    - Validates the state parameter against the pending set (CSRF check).
    - Exchanges the authorization code for access and refresh tokens.
    - Saves tokens to the database.
    """
    # Outreach rejected authorization (e.g. user clicked "Deny")
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Outreach authorization failed: {error}",
        )

    # CSRF check: state must match one we generated in /start
    if not state or state not in _pending_states:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter (CSRF check failed). Start auth again at /auth/outreach/start",
        )
    _pending_states.discard(state)

    # Exchange authorization code for tokens
    try:
        response = httpx.post(
            OUTREACH_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.OUTREACH_CLIENT_ID,
                "client_secret": settings.OUTREACH_CLIENT_SECRET,
                "redirect_uri": settings.OUTREACH_REDIRECT_URI,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Outreach token exchange failed: {e.response.text}")
        raise HTTPException(
            status_code=502,
            detail=f"Outreach token exchange failed: {e.response.text}",
        )

    from datetime import datetime, timezone, timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
    save_tokens(data["access_token"], data["refresh_token"], expires_at)
    logger.info("Outreach OAuth authorized successfully")

    return {"status": "authorized", "expires_at": expires_at.isoformat()}
```

**Step 4: Register the auth router in main.py**

In `api/main.py`:

Add to imports at the top:
```python
from api.routers import auth
```

Add after the existing `app.include_router(health.router)` line:
```python
app.include_router(auth.router)
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_api.py::TestOutreachAuthRouter -v
```

Expected: all 3 PASS

**Step 6: Commit**

```bash
git add api/routers/auth.py api/main.py tests/test_api.py
git commit -m "feat: add Outreach OAuth auth router (/auth/outreach/start, /auth/outreach/callback)"
```

---

### Task 9: Create outreach router

**Files:**
- Create: `api/routers/outreach.py`

**Step 1: Write the failing tests**

Add to `tests/test_api.py`:

```python
class TestOutreachRouter:
    """Tests for Outreach sync endpoints"""

    def test_sync_returns_401_when_not_authorized(self):
        """POST /api/v1/outreach/sync returns 401 when no tokens exist"""
        from fastapi.testclient import TestClient
        from api.main import app
        from unittest.mock import patch
        client = TestClient(app)
        with patch("api.outreach_client.load_tokens", return_value=None):
            response = client.post("/api/v1/outreach/sync")
        assert response.status_code == 401

    def test_status_returns_unauthorized_state(self):
        """GET /api/v1/outreach/status returns authorized=False when no tokens"""
        from fastapi.testclient import TestClient
        from api.main import app
        from unittest.mock import patch
        client = TestClient(app)
        with patch("api.outreach_client.load_tokens", return_value=None):
            response = client.get("/api/v1/outreach/status")
        assert response.status_code == 200
        assert response.json()["authorized"] is False
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py::TestOutreachRouter -v
```

Expected: FAIL — router not registered yet

**Step 3: Create api/routers/outreach.py**

```python
"""
Outreach sync endpoints.
Provides manual sync trigger and status reporting.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from api.outreach_client import (
    get_last_synced_at,
    is_authorized,
    load_tokens,
    run_sync,
)
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
    if not is_authorized():
        raise HTTPException(
            status_code=401,
            detail="Not authorized with Outreach. Visit /auth/outreach/start to authenticate.",
        )
    count = run_sync()
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
    tokens = load_tokens()
    return OutreachStatus(
        authorized=tokens is not None,
        last_synced_at=get_last_synced_at(),
        token_expires_at=tokens["expires_at"] if tokens else None,
        next_scheduled_run=get_next_run_time(),
        poll_interval_minutes=settings.OUTREACH_POLL_INTERVAL_MINUTES,
    )
```

**Step 4: Register the outreach router in main.py**

In `api/main.py`:

Update the import line to include outreach:
```python
from api.routers import auth, outreach
```

Add after `app.include_router(auth.router)`:
```python
app.include_router(outreach.router)
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_api.py::TestOutreachRouter -v
```

Expected: all 2 PASS

**Step 6: Commit**

```bash
git add api/routers/outreach.py api/main.py tests/test_api.py
git commit -m "feat: add Outreach sync and status endpoints"
```

---

### Task 10: Wire scheduler into FastAPI lifespan

**Files:**
- Modify: `api/main.py`

**Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
class TestSchedulerLifespan:
    """Verify scheduler starts and stops with the FastAPI app"""

    def test_scheduler_starts_with_app(self):
        """Scheduler should be running when app is live"""
        from fastapi.testclient import TestClient
        from api.main import app
        from api import scheduler as sched_module
        with TestClient(app):
            from api.scheduler import scheduler
            assert scheduler.running
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py::TestSchedulerLifespan -v
```

Expected: FAIL — scheduler not started in lifespan yet

**Step 3: Update lifespan in api/main.py**

In `api/main.py`, update the imports at the top to add:
```python
from api.scheduler import start_scheduler, stop_scheduler
```

Update the `lifespan` function — add `start_scheduler()` before `yield` and `stop_scheduler()` after `yield`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Project Rift API v{__version__}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"Rate limit: {settings.RATE_LIMIT_PER_MINUTE} requests/minute")
    start_scheduler()

    yield

    logger.info("Shutting down Project Rift API")
    stop_scheduler()
    cleanup_database_connections()
    logger.info("Database connections closed")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_api.py::TestSchedulerLifespan -v
```

Expected: PASS

**Step 5: Run the full test suite**

```bash
make test
```

Expected: all existing tests still pass, new tests pass

**Step 6: Commit**

```bash
git add api/main.py tests/test_api.py
git commit -m "feat: start/stop Outreach scheduler in FastAPI lifespan"
```

---

### Task 11: Final integration check

**Step 1: Format and lint**

```bash
make format
make lint
```

Fix any issues reported.

**Step 2: Run full test suite**

```bash
make test
```

Expected: all tests pass

**Step 3: Start the API and verify endpoints exist**

```bash
make start-api
```

In another terminal:
```bash
curl http://localhost:8000/api/v1/outreach/status
# Expected: {"authorized": false, "last_synced_at": null, ...}

curl http://localhost:8000/docs
# Expected: /auth/outreach/start, /auth/outreach/callback, /api/v1/outreach/sync, /api/v1/outreach/status visible
```

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete Outreach OAuth integration with polling scheduler"
```
