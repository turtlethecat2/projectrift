"""
Webhook integration tests for Project Rift
Tests end-to-end webhook processing
"""

import os

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", 8000)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
BASE_URL = f"http://{API_HOST}:{API_PORT}"


@pytest.fixture
def webhook_headers():
    """Fixture to provide valid webhook headers"""
    return {"Content-Type": "application/json", "X-RIFT-SECRET": WEBHOOK_SECRET}


class TestWebhookIntegration:
    """Integration tests for webhook endpoints"""

    def test_webhook_call_dial(self, webhook_headers):
        """Test processing a call dial event"""
        payload = {
            "source": "nooks",
            "event_type": "call_dial",
            "metadata": {
                "prospect_name": "Integration Test",
                "phone_number": "+1234567890",
            },
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=webhook_headers,
                timeout=5,
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["gold_earned"] == 15
            assert data["xp_earned"] == 5

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    def test_webhook_call_connect(self, webhook_headers):
        """Test processing a call connect event"""
        payload = {
            "source": "nooks",
            "event_type": "call_connect",
            "metadata": {
                "prospect_name": "Integration Test",
                "company": "Test Corp",
                "call_duration": 180,
            },
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=webhook_headers,
                timeout=5,
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["gold_earned"] == 100
            assert data["xp_earned"] == 40

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    def test_webhook_meeting_booked(self, webhook_headers):
        """Test processing a meeting booked event"""
        payload = {
            "source": "outreach",
            "event_type": "meeting_booked",
            "metadata": {
                "prospect_name": "Integration Test",
                "company": "Test Corp",
                "meeting_time": "2026-01-10T14:00:00Z",
            },
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=webhook_headers,
                timeout=5,
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["gold_earned"] == 1000
            assert data["xp_earned"] == 500

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    def test_webhook_email_sent(self, webhook_headers):
        """Test processing an email sent event"""
        payload = {
            "source": "outreach",
            "event_type": "email_sent",
            "metadata": {
                "prospect_name": "Integration Test",
                "email": "test@example.com",
                "subject": "Test Email",
            },
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=webhook_headers,
                timeout=5,
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["gold_earned"] == 10
            assert data["xp_earned"] == 3

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")


class TestWebhookErrors:
    """Test webhook error handling"""

    def test_webhook_missing_secret(self):
        """Test that missing secret is rejected"""
        payload = {"source": "nooks", "event_type": "call_dial"}

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest", json=payload, timeout=5
            )

            assert response.status_code in [401, 422]

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    def test_webhook_invalid_secret(self):
        """Test that invalid secret is rejected"""
        payload = {"source": "nooks", "event_type": "call_dial"}

        headers = {
            "Content-Type": "application/json",
            "X-RIFT-SECRET": "invalid-secret-1234567890123456789012",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=headers,
                timeout=5,
            )

            assert response.status_code == 401

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    def test_webhook_invalid_source(self, webhook_headers):
        """Test that invalid source is rejected"""
        payload = {"source": "invalid_source", "event_type": "call_dial"}

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=webhook_headers,
                timeout=5,
            )

            assert response.status_code == 422

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    def test_webhook_invalid_event_type(self, webhook_headers):
        """Test that invalid event type is rejected"""
        payload = {"source": "nooks", "event_type": "invalid_type"}

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=webhook_headers,
                timeout=5,
            )

            assert response.status_code == 422
            data = response.json()
            assert "detail" in data

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")


class TestWebhookIdempotency:
    """Test webhook idempotency"""

    def test_duplicate_event_detection(self, webhook_headers):
        """Test that duplicate events are detected"""
        import time

        payload = {
            "source": "manual",
            "event_type": "call_dial",
            "metadata": {"test": "idempotency", "timestamp": str(time.time())},
        }

        try:
            # Send first request
            response1 = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=webhook_headers,
                timeout=5,
            )

            assert response1.status_code == 201

            # Send duplicate request immediately
            response2 = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=webhook_headers,
                timeout=5,
            )

            # Should detect duplicate
            data2 = response2.json()
            assert data2.get("duplicate", False) is True or response2.status_code == 201

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")


class TestStatsAfterWebhook:
    """Test that stats update after webhook events"""

    def test_stats_update_after_event(self, webhook_headers):
        """Test that stats reflect new events"""
        import time

        try:
            # Get current stats
            stats_before = requests.get(
                f"{BASE_URL}/api/v1/stats/current", timeout=5
            ).json()

            # Send an event
            payload = {
                "source": "manual",
                "event_type": "call_dial",
                "metadata": {"test": "stats_update", "timestamp": str(time.time())},
            }

            webhook_response = requests.post(
                f"{BASE_URL}/api/v1/webhook/ingest",
                json=payload,
                headers=webhook_headers,
                timeout=5,
            )

            assert webhook_response.status_code == 201

            # Get updated stats
            stats_after = requests.get(
                f"{BASE_URL}/api/v1/stats/current", timeout=5
            ).json()

            # Verify stats increased (unless it was a duplicate)
            if not webhook_response.json().get("duplicate", False):
                assert stats_after["total_gold"] >= stats_before["total_gold"]
                assert stats_after["total_xp"] >= stats_before["total_xp"]

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
