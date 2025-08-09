"""
Unit tests for Celery background tasks.

Tests the agent polling task functionality, error handling,
and GraphQL communication using mocked HTTP requests.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import django
import httpx
import pytest
from django.test import override_settings

from app.server.monitoring.tasks import poll_agent_telemetry

# Add the server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../app/server"))

# Configure Django settings with correct path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server_config.settings")

# Initialize Django
django.setup()


@pytest.fixture
def mock_httpx_client():
    """Create a mocked httpx.Client for HTTP requests."""
    with patch("app.server.monitoring.tasks.httpx.Client") as mock_client:
        mock_client_instance = MagicMock()
        mock_client.return_value.__enter__.return_value = mock_client_instance
        mock_client.return_value.__exit__.return_value = None
        yield mock_client_instance


@pytest.fixture
def mock_query_loader():
    """Create a mocked GraphQL query loader."""
    with patch("app.server.monitoring.tasks.get_query") as mock_get_query:
        mock_get_query.return_value = "query GetBasicTelemetry { telemetry { timestamp } }"
        yield mock_get_query


@pytest.fixture
def success_response():
    """Mock successful GraphQL response data."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "telemetry": {
                "timestamp": 1641024000.0,
                "system": {"hostname": "test-agent"},
                "cpu": {"usage_percent": 45.2, "name": "Test CPU"},
                "memory": {"ram_percent": 60.0},
            }
        }
    }
    return mock_response


class TestAgentPollingTask:
    """Test the agent telemetry polling Celery task."""

    @override_settings(AGENT_BASE_URL="http://localhost:8001", AGENT_TIMEOUT=5)
    def test_poll_agent_success(self, mock_httpx_client, mock_query_loader, success_response):
        """Test successful agent polling and data extraction."""
        # Configure the mock HTTP client
        mock_httpx_client.post.return_value = success_response

        # Execute the task
        result = poll_agent_telemetry()

        # Verify the result
        assert result["status"] == "success"
        assert result["hostname"] == "test-agent"
        assert result["timestamp"] == 1641024000.0
        assert result["data_received"] is True

        # Verify HTTP client was called correctly
        mock_httpx_client.post.assert_called_once_with(
            "http://localhost:8001/graphql",
            json={"query": "query GetBasicTelemetry { telemetry { timestamp } }"},
            headers={"Content-Type": "application/json"},
        )

    @override_settings(AGENT_BASE_URL="http://localhost:8001", AGENT_TIMEOUT=5)
    def test_poll_agent_graphql_errors(self, mock_httpx_client, mock_query_loader):
        """Test handling of GraphQL errors in response."""
        # Mock response with GraphQL errors
        error_response = MagicMock()
        error_response.status_code = 200
        error_response.json.return_value = {"errors": [{"message": 'Field "invalid" not found'}]}
        mock_httpx_client.post.return_value = error_response

        result = poll_agent_telemetry()

        assert result["status"] == "error"
        assert result["message"] == "GraphQL errors"

    @override_settings(AGENT_BASE_URL="http://localhost:8001", AGENT_TIMEOUT=5)
    def test_poll_agent_http_error(self, mock_httpx_client, mock_query_loader):
        """Test handling of HTTP errors (agent server down)."""
        # Mock HTTP error response
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        mock_httpx_client.post.return_value = error_response

        result = poll_agent_telemetry()

        assert result["status"] == "error"
        assert "HTTP 500" in result["message"]

    @override_settings(AGENT_BASE_URL="http://localhost:8001", AGENT_TIMEOUT=5)
    def test_poll_agent_timeout(self, mock_httpx_client, mock_query_loader):
        """Test handling of agent timeout (agent offline)."""
        # Mock timeout exception
        mock_httpx_client.post.side_effect = httpx.TimeoutException("Request timeout")

        result = poll_agent_telemetry()

        assert result["status"] == "timeout"
        assert "Agent offline or unreachable" in result["message"]

    @override_settings(AGENT_BASE_URL="http://localhost:8001", AGENT_TIMEOUT=5)
    def test_poll_agent_no_telemetry_data(self, mock_httpx_client, mock_query_loader):
        """Test handling when response contains no telemetry data."""
        # Mock response with empty data
        empty_response = MagicMock()
        empty_response.status_code = 200
        empty_response.json.return_value = {"data": {"telemetry": None}}
        mock_httpx_client.post.return_value = empty_response

        result = poll_agent_telemetry()

        assert result["status"] == "warning"
        assert result["message"] == "No telemetry data"

    @override_settings(AGENT_BASE_URL="http://localhost:8001", AGENT_TIMEOUT=5)
    def test_poll_agent_unexpected_exception(self, mock_query_loader):
        """Test handling of unexpected exceptions."""
        # Mock unexpected exception during query loading
        mock_query_loader.side_effect = Exception("Unexpected error")

        result = poll_agent_telemetry()

        assert result["status"] == "error"
        assert "Unexpected error" in result["message"]

    @override_settings(AGENT_BASE_URL="http://custom-agent:9000", AGENT_TIMEOUT=10)
    def test_task_uses_configured_settings(self, mock_query_loader):
        """Test that task uses Django settings for configuration."""
        with patch("app.server.monitoring.tasks.httpx.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.post.side_effect = httpx.ConnectError("Connection failed")
            mock_client.return_value.__enter__.return_value = mock_client_instance
            mock_client.return_value.__exit__.return_value = None

            poll_agent_telemetry()

            # Verify timeout was passed to httpx.Client
            mock_client.assert_called_once_with(timeout=10)
