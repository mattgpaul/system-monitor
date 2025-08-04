"""
Unit tests for the FastAPI application.

Tests the FastAPI app setup, REST endpoints, and GraphQL integration
without testing the actual GraphQL resolvers.
"""

import pytest
from fastapi.testclient import TestClient

from app.agent.api import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestFastAPIApplication:
    """Test FastAPI application setup and configuration."""

    def test_app_metadata(self):
        """Test that FastAPI app has correct metadata."""
        assert app.title == "System Telemetry Agent"
        assert "GraphQL API for system monitoring" in app.description
        assert app.version == "0.1.0"  # From your __init__.py

    def test_app_has_routes(self):
        """Test that required routes are registered."""
        route_paths = [route.path for route in app.routes]
        assert "/" in route_paths
        assert "/health" in route_paths
        assert "/graphql" in route_paths


class TestRESTEndpoints:
    """Test the REST API endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "System Telemetry Agent"
        assert data["graphql_endpoint"] == "/graphql"
        assert data["health_endpoint"] == "/health"
        assert data["documentation"] == "/docs"
        assert "version" in data

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "OK"
        assert "version" in data

    def test_docs_endpoint_exists(self, client):
        """Test that FastAPI auto-generated docs are available."""
        response = client.get("/docs")
        assert response.status_code == 200
        # FastAPI serves HTML for docs
        assert "text/html" in response.headers["content-type"]


class TestGraphQLEndpoint:
    """Test GraphQL endpoint integration (not the actual queries)."""

    def test_graphql_endpoint_exists(self, client):
        """Test that GraphQL endpoint is available."""
        # GraphQL endpoint should accept POST requests
        response = client.post("/graphql", json={"query": "{ __typename }"})
        assert response.status_code == 200

    def test_graphql_introspection(self, client):
        """Test GraphQL introspection query works."""
        query = """
        query {
            __schema {
                queryType {
                    name
                }
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["__schema"]["queryType"]["name"] == "Query"

    def test_graphql_supports_get_requests(self, client):
        """Test that GraphQL endpoint supports GET requests for queries."""
        response = client.get("/graphql?query={__typename}")
        assert response.status_code == 200
