# api/CLAUDE.md

FastAPI backend for webhook ingestion and stats endpoints.

## Structure

```
main.py       → App entry point, CORS, middleware, lifespan events
config.py     → Pydantic Settings (validates .env, min secret length)
schemas.py    → Request/response Pydantic models
security.py   → Webhook auth (X-RIFT-SECRET), rate limiting (SlowAPI)
database.py   → Connection pool management
routers/
  webhook.py  → POST /api/v1/webhook/ingest
  health.py   → GET /api/v1/health, /api/v1/stats/current
```

## Key Patterns

**Authentication:** `verify_webhook_secret` dependency in `security.py` uses constant-time comparison via `secrets.compare_digest()`.

**Rate Limiting:** SlowAPI with per-IP limits. Configured in `security.py`:
- Webhooks: 60/min (configurable via `RATE_LIMIT_PER_MINUTE`)
- Health: 100/min
- Stats: 120/min

**Schemas:** All request/response types defined in `schemas.py`. Always add new schemas here, not inline.

**Allowed Event Types:** `call_dial`, `call_connect`, `email_sent`, `meeting_booked`, `meeting_attended` (validated in `EventPayload` schema)

**Allowed Sources:** `outreach`, `nooks`, `manual`, `zapier` (regex validated in `EventPayload`)

## Adding a New Endpoint

1. Create route in appropriate router file (or new file in `routers/`)
2. Define Pydantic schemas in `schemas.py`
3. Add router to `main.py` via `app.include_router()`
4. Add tests in `tests/test_api.py`

## Running

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Docs

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic v2: https://docs.pydantic.dev/latest/
- SlowAPI: https://github.com/laurentS/slowapi
