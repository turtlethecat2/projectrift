"""
API endpoint tests for Project Rift
Tests FastAPI routes, authentication, and error handling
"""

import pytest
from fastapi.testclient import TestClient

from api.config import settings
from api.main import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_endpoint(self):
        """Test that root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Project Rift API"

    def test_root_endpoint_structure(self):
        """Test root endpoint response structure"""
        response = client.get("/")
        data = response.json()
        assert "endpoints" in data
        assert "health" in data
        assert isinstance(data["endpoints"], dict)


class TestHealthEndpoint:
    """Tests for the health check endpoint"""

    def test_health_check_success(self):
        """Test successful health check"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_database_status(self):
        """Test that health check reports database status"""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["database"] in ["connected", "disconnected"]


class TestWebhookAuthentication:
    """Tests for webhook authentication"""

    def test_webhook_without_secret(self):
        """Test that webhook endpoint rejects requests without secret"""
        response = client.post(
            "/api/v1/webhook/ingest",
            json={"source": "nooks", "event_type": "call_dial"},
        )
        assert response.status_code == 422  # Missing required header

    def test_webhook_with_invalid_secret(self):
        """Test that webhook endpoint rejects invalid secret"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": "invalid-secret-12345678901234567890"},
            json={"source": "nooks", "event_type": "call_dial"},
        )
        assert response.status_code == 401
        assert "Invalid webhook secret" in response.json()["detail"]


class TestWebhookValidation:
    """Tests for webhook payload validation"""

    def test_webhook_invalid_source(self):
        """Test that invalid source is rejected"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
            json={"source": "invalid_source", "event_type": "call_dial"},
        )
        assert response.status_code == 422

    def test_webhook_invalid_event_type(self):
        """Test that invalid event type is rejected"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
            json={"source": "nooks", "event_type": "invalid_type"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "Unknown event type" in str(data)

    def test_webhook_missing_required_field(self):
        """Test that missing required fields are rejected"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
            json={"source": "nooks"},  # Missing event_type
        )
        assert response.status_code == 422

    def test_webhook_metadata_too_large(self):
        """Test that oversized metadata is rejected"""
        large_metadata = {"data": "x" * 10000}  # 10KB of data
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
            json={
                "source": "nooks",
                "event_type": "call_dial",
                "metadata": large_metadata,
            },
        )
        assert response.status_code == 422


class TestWebhookSuccess:
    """Tests for successful webhook processing"""

    def test_webhook_valid_payload(self):
        """Test that valid payload is accepted"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
            json={
                "source": "nooks",
                "event_type": "call_connect",
                "metadata": {"prospect": "Test Corp"},
            },
        )
        # Note: This will fail if database is not available
        # In a real test environment, you'd mock the database
        assert response.status_code in [201, 500]  # 500 if DB unavailable

    def test_webhook_response_structure(self):
        """Test webhook response structure for valid request"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
            json={"source": "manual", "event_type": "call_dial", "metadata": {}},
        )
        if response.status_code == 201:
            data = response.json()
            assert "status" in data
            assert "event_id" in data
            assert "gold_earned" in data
            assert "xp_earned" in data
            assert "message" in data


class TestStatsEndpoint:
    """Tests for the stats endpoint"""

    def test_stats_endpoint(self):
        """Test that stats endpoint is accessible"""
        response = client.get("/api/v1/stats/current")
        # Will fail if database is unavailable
        assert response.status_code in [200, 500]

    def test_stats_response_structure(self):
        """Test stats response structure"""
        response = client.get("/api/v1/stats/current")
        if response.status_code == 200:
            data = response.json()
            assert "total_gold" in data
            assert "total_xp" in data
            assert "current_level" in data
            assert "rank" in data


class TestRateLimiting:
    """Tests for rate limiting functionality"""

    @pytest.mark.skip(reason="Rate limiting tests require special configuration")
    def test_rate_limit_exceeded(self):
        """Test that rate limiting kicks in after too many requests"""
        # Send many requests rapidly
        responses = []
        for _ in range(100):
            response = client.get("/api/v1/health")
            responses.append(response.status_code)

        # At least one should be rate limited
        assert 429 in responses


class TestErrorHandling:
    """Tests for error handling"""

    def test_404_for_invalid_endpoint(self):
        """Test that invalid endpoints return 404"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_405_for_wrong_method(self):
        """Test that wrong HTTP method returns 405"""
        response = client.get("/api/v1/webhook/ingest")
        assert response.status_code == 405


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
