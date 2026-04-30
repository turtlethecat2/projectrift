# tests/CLAUDE.md

Pytest test suite for Project Rift.

## Structure

```
test_api.py       → API endpoint tests (routes, auth, validation)
test_database.py  → Database query tests
test_webhooks.py  → Webhook integration tests
```

## Running Tests

```bash
make test                              # All tests with coverage
pytest tests/ -v                       # Verbose output
pytest tests/test_api.py -v            # Single file
pytest tests/test_api.py::TestHealthEndpoint -v  # Single class
pytest tests/test_api.py::TestHealthEndpoint::test_health_check_success -v  # Single test
pytest tests/ --cov=api --cov=app      # With coverage report
```

## Test Patterns

**API Tests:** Use `TestClient` from FastAPI:
```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
response = client.get("/api/v1/health")
```

**Authenticated Requests:** Include the secret header:
```python
response = client.post(
    "/api/v1/webhook/ingest",
    headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
    json={"source": "nooks", "event_type": "call_dial"}
)
```

**Database Tests:** Some tests require a running database. They may return 500 if DB unavailable - this is expected in CI without a test DB.

## Test Organization

Tests are organized by class:
- `TestRootEndpoint` - Root `/` endpoint
- `TestHealthEndpoint` - Health check
- `TestWebhookAuthentication` - Auth failures
- `TestWebhookValidation` - Payload validation
- `TestWebhookSuccess` - Happy path
- `TestStatsEndpoint` - Stats retrieval
- `TestRateLimiting` - Rate limit behavior (skipped by default)
- `TestErrorHandling` - 404, 405 responses

## Adding Tests

1. Add test class or method to appropriate file
2. Use descriptive names: `test_<what>_<expected_behavior>`
3. Include docstring explaining what's being tested
4. Mock database if testing logic that doesn't need real DB

## Docs

- pytest: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
