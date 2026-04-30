# Outreach OAuth Integration Design

**Date:** 2026-02-22
**Status:** Approved

## Overview

Full Outreach OAuth 2.0 integration for Project Rift. Authorizes the app to pull call and meeting data from Outreach, stores tokens in PostgreSQL, and ingests activity as gamification events via scheduled polling (CT business hours, weekdays) with a manual sync endpoint.

---

## Architecture

### New Files

| File | Purpose |
|---|---|
| `api/routers/auth.py` | `GET /auth/outreach/start`, `GET /auth/outreach/callback` |
| `api/routers/outreach.py` | `POST /api/v1/outreach/sync`, `GET /api/v1/outreach/status` |
| `api/outreach_client.py` | Outreach API client — fetch calls/meetings, token refresh, activity mapping |
| `api/scheduler.py` | APScheduler setup + poll job definition |
| `database/migrations/004_oauth_tokens.sql` | Token + sync state table |

### Modified Files

| File | Change |
|---|---|
| `api/config.py` | Add `OUTREACH_CLIENT_ID`, `OUTREACH_CLIENT_SECRET`, `OUTREACH_REDIRECT_URI`, `OUTREACH_POLL_INTERVAL_MINUTES` |
| `api/main.py` | Register new routers; start/stop scheduler in lifespan |
| `api/schemas.py` | Add sync status/response schemas |

---

## OAuth Flow

```
Browser → GET /auth/outreach/start
        → Generates random state token, stores in session
        → 302 redirect to Outreach authorization URL
          (client_id, redirect_uri, scope, response_type=code, state)

Outreach → GET /auth/outreach/callback?code=ABC123&state=XYZ
         → Verify state matches session (CSRF protection)
         → Exchange code for tokens via POST https://api.outreach.io/oauth/token
         → Upsert access_token, refresh_token, expires_at into oauth_tokens table
         → Return JSON: {"status": "authorized", "expires_at": "..."}

Error path:
         → GET /auth/outreach/callback?error=access_denied
         → Return 400 with Outreach error message, skip token exchange

Scopes: calls.read meetings.read
Token endpoint: https://api.outreach.io/oauth/token
```

### Token Refresh Strategy

- In-memory cache holds tokens for the duration of a poll cycle (avoids repeated DB reads)
- Cache is invalidated after any refresh
- Proactive refresh: at scheduler startup and after each poll, if `expires_at < now + 10min`, refresh immediately
- On refresh failure: log error, skip poll cycle, retain `last_synced_at` so next cycle retries the same window

---

## Data Model

```sql
CREATE TABLE oauth_tokens (
    id            SERIAL PRIMARY KEY,
    provider      VARCHAR(50) NOT NULL UNIQUE DEFAULT 'outreach',
    access_token  TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at    TIMESTAMPTZ NOT NULL,
    last_synced_at TIMESTAMPTZ,   -- high-water mark for polling window
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);
```

- Single row per provider, upserted via `ON CONFLICT (provider) DO UPDATE`
- `last_synced_at` tracks the upper bound of the last successful poll; next poll fetches activities created after this timestamp

---

## Polling Scheduler

**Schedule:** APScheduler `CronTrigger`, Mon–Fri, 8am–5pm `America/Chicago`, every `OUTREACH_POLL_INTERVAL_MINUTES` (default: 15)

**Poll job sequence:**
1. Load tokens from DB (or in-memory cache if fresh)
2. Proactively refresh if `expires_at < now + 10min`
3. Fetch calls from `GET /api/v2/calls` created after `last_synced_at`
4. Fetch meetings from `GET /api/v2/meetings` created after `last_synced_at`
5. Map each activity to `EventPayload`, call webhook ingest logic directly (not over HTTP)
6. Update `last_synced_at` to `now` on success
7. Log count of events ingested

**Manual sync:**
- `POST /api/v1/outreach/sync` — runs the same poll job immediately, returns ingestion count
- `GET /api/v1/outreach/status` — returns `last_synced_at`, token expiry, next scheduled run time
- Returns 401 if not yet authorized, directing user to `/auth/outreach/start`

---

## Activity Mapping

All field name assumptions are isolated in constants at the top of `outreach_client.py` for easy adjustment:

```python
# Outreach API v2: GET /api/v2/calls
# Docs: https://api.outreach.io/api/v2/docs#call
OUTREACH_CALL_ANSWERED_FIELD = "answeredAt"   # null if unanswered, timestamp if connected
OUTREACH_MEETING_RESOURCE    = "meetings"      # endpoint: /api/v2/meetings
```

| Outreach Resource | Condition | Project Rift Event |
|---|---|---|
| `GET /api/v2/calls` | any call record | `call_dial` |
| `GET /api/v2/calls` | `answeredAt` is not null | `call_connect` |
| `GET /api/v2/meetings` | any meeting record | `meeting_booked` |

- A single answered call produces two events (`call_dial` + `call_connect`)
- All events use `source: "outreach"` (already in allowed sources)
- Existing 5-minute dedup window in `raw_events` prevents double-counting across poll cycles

---

## Error Handling

| Scenario | Behavior |
|---|---|
| OAuth callback receives `?error=` | Return 400 with Outreach error message; skip token exchange |
| Token refresh fails | Log error, skip poll cycle, do not update `last_synced_at` |
| Outreach API returns 4xx/5xx | Log error + status code, skip that activity type, continue with others |
| Poll job throws unexpected exception | APScheduler catches and logs; next run scheduled normally |
| Manual sync called without authorization | Return 401, direct user to `/auth/outreach/start` |
