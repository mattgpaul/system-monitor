"""
Unit tests for GraphQL query loading and management.

Tests the query file loading, caching, and error handling
for the monitoring GraphQL queries.
"""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.server.monitoring.graphql_queries import (
    QUERY_TYPES,
    get_available_queries,
    get_query,
    load_query_file,
    reload_queries,
)


class TestQueryLoading:
    """Test GraphQL query file loading functionality."""

    def test_get_available_queries(self):
        """Test that all expected query types are available."""
        available = get_available_queries()
        expected = ["basic", "extended", "health"]

        assert isinstance(available, list)
        assert set(available) == set(expected)

    def test_get_basic_query(self):
        """Test loading the basic telemetry query."""
        query = get_query("basic")

        assert isinstance(query, str)
        assert "GetBasicTelemetry" in query
        assert "telemetry" in query
        assert "cpu" in query
        assert "memory" in query

    def test_get_extended_query(self):
        """Test loading the extended telemetry query."""
        query = get_query("extended")

        assert isinstance(query, str)
        assert "GetExtendedTelemetry" in query
        assert "gpu" in query
        assert "network" in query
        assert "system" in query

    def test_get_health_query(self):
        """Test loading the health check query."""
        query = get_query("health")

        assert isinstance(query, str)
        assert "GetAgentHealth" in query
        assert "timestamp" in query

    def test_get_query_invalid_type(self):
        """Test error handling for invalid query types."""
        with pytest.raises(ValueError) as exc_info:
            get_query("nonexistent")

        assert "Unknown query type" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_get_query_default_basic(self):
        """Test that default query type is 'basic'."""
        default_query = get_query()
        basic_query = get_query("basic")

        assert default_query == basic_query

    @patch("app.server.monitoring.graphql_queries.QUERIES_DIR")
    @patch("builtins.open", new_callable=mock_open, read_data="query Test { field }")
    def test_load_query_file_success(self, mock_file, mock_queries_dir):
        """Test successful query file loading."""
        # Mock the path and its exists method
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_queries_dir.__truediv__.return_value = mock_path

        result = load_query_file("test_query")

        assert result == "query Test { field }"
        mock_file.assert_called_once()

    @patch("app.server.monitoring.graphql_queries.QUERIES_DIR")
    def test_load_query_file_not_found(self, mock_queries_dir):
        """Test error handling when query file doesn't exist."""
        # Mock the path to return a non-existent file
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_queries_dir.__truediv__.return_value = mock_path

        with pytest.raises(FileNotFoundError) as exc_info:
            load_query_file("nonexistent_query")

        assert "Query file not found" in str(exc_info.value)

    def test_query_types_mapping(self):
        """Test that QUERY_TYPES mapping is correct."""
        expected_mapping = {
            "basic": "telemetry_basic",
            "extended": "telemetry_extended",
            "health": "health_check",
        }

        assert QUERY_TYPES == expected_mapping

    def test_reload_queries_functionality(self):
        """Test that reload_queries function exists and is callable."""
        # Should not raise an exception
        reload_queries()

        # Queries should still be available after reload
        available = get_available_queries()
        assert len(available) > 0
