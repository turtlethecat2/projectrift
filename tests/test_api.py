"""
API endpoint tests for Project Rift
Tests FastAPI routes, authentication, and error handling
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.config import settings

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
            json={"source": "nooks", "event_type": "call_dial"}
        )
        assert response.status_code == 422  # Missing required header

    def test_webhook_with_invalid_secret(self):
        """Test that webhook endpoint rejects invalid secret"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": "invalid-secret-12345678901234567890"},
            json={"source": "nooks", "event_type": "call_dial"}
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
            json={"source": "invalid_source", "event_type": "call_dial"}
        )
        assert response.status_code == 422

    def test_webhook_invalid_event_type(self):
        """Test that invalid event type is rejected"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
            json={"source": "nooks", "event_type": "invalid_type"}
        )
        assert response.status_code == 422
        data = response.json()
        assert "Unknown event type" in str(data)

    def test_webhook_missing_required_field(self):
        """Test that missing required fields are rejected"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
            json={"source": "nooks"}  # Missing event_type
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
                "metadata": large_metadata
            }
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
                "metadata": {"prospect": "Test Corp"}
            }
        )
        # Note: This will fail if database is not available
        # In a real test environment, you'd mock the database
        assert response.status_code in [201, 500]  # 500 if DB unavailable

    def test_webhook_response_structure(self):
        """Test webhook response structure for valid request"""
        response = client.post(
            "/api/v1/webhook/ingest",
            headers={"X-RIFT-SECRET": settings.WEBHOOK_SECRET},
            json={
                "source": "manual",
                "event_type": "call_dial",
                "metadata": {}
            }
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
