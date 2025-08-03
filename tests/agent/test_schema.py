"""
Unit tests for the GraphQL schema.

Tests the GraphQL resolvers, queries, and data transformations
using mocked telemetry collectors.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agent.api import app
from app.agent.schema import Query
from app.agent.telemetry import (
    CPUMetrics,
    GPUMetrics,
    MemoryMetrics,
    NetworkMetrics,
    SystemMetrics,
    TelemetryData,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_collector(mocker):
    """Create a mocked TelemetryCollector."""
    collector = MagicMock()

    # Mock individual collection methods
    collector.collect_cpu_metrics = AsyncMock(
        return_value=CPUMetrics(
            name="Test CPU",
            temperature=45.0,
            usage_percent=25.5,
            core_usage=[20.0, 30.0],
            frequency=3400.0,
        )
    )

    collector.collect_gpu_metrics = AsyncMock(
        return_value=GPUMetrics(
            name="Test GPU",
            temperature=65.0,
            usage_percent=80.0,
            memory_used=8000,
            memory_total=24000,
            fan_speed=1500,
            clock_speed="2100",
        )
    )

    collector.collect_memory_metrics = AsyncMock(
        return_value=MemoryMetrics(
            ram_used=16000000000,
            ram_total=32000000000,
            ram_percent=50.0,
            disk_used=500000000000,
            disk_total=1000000000000,
            disk_percent=50.0,
        )
    )

    collector.collect_network_metrics = AsyncMock(
        return_value=[
            NetworkMetrics(
                interface="eth0",
                ip_address="192.168.1.100",
                bytes_sent=1000000,
                bytes_received=2000000,
                packets_sent=500,
                packets_received=800,
                speed_upload=1024.0,
                speed_download=2048.0,
            )
        ]
    )

    collector.collect_system_metrics = AsyncMock(
        return_value=SystemMetrics(
            hostname="test-machine",
            os_name="Ubuntu 22.04",
            kernel_version="6.8.0",
            uptime_seconds=86400,
            user="testuser",
            boot_time=1703980800.0,
        )
    )

    # Mock full collection
    collector.collect_all_metrics = AsyncMock(
        return_value=TelemetryData(
            timestamp=1704067200.0,
            cpu=collector.collect_cpu_metrics.return_value,
            gpu=collector.collect_gpu_metrics.return_value,
            memory=collector.collect_memory_metrics.return_value,
            network=collector.collect_network_metrics.return_value,
            system=collector.collect_system_metrics.return_value,
        )
    )

    return collector


class TestGraphQLResolvers:
    """Test individual GraphQL resolvers."""

    def test_cpu_resolver(self, client, mock_collector, mocker):
        """Test CPU resolver returns correct data and calls right method."""
        mocker.patch("app.agent.api.collector_instance", mock_collector)

        query = """
        query {
            cpu {
                name
                temperature
                usagePercent
                coreUsage
                frequency
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        cpu_data = data["data"]["cpu"]

        assert cpu_data["name"] == "Test CPU"
        assert cpu_data["temperature"] == 45.0
        assert cpu_data["usagePercent"] == 25.5
        assert cpu_data["coreUsage"] == [20.0, 30.0]
        assert cpu_data["frequency"] == 3400.0

        # Verify only CPU method was called
        mock_collector.collect_cpu_metrics.assert_called_once()
        mock_collector.collect_gpu_metrics.assert_not_called()
        mock_collector.collect_memory_metrics.assert_not_called()

    def test_gpu_resolver(self, client, mock_collector, mocker):
        """Test GPU resolver returns correct data."""
        mocker.patch("app.agent.api.collector_instance", mock_collector)

        query = """
        query {
            gpu {
                name
                temperature
                usagePercent
                memoryUsed
                memoryTotal
                fanSpeed
                clockSpeed
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200

        data = response.json()
        gpu_data = data["data"]["gpu"]

        assert gpu_data["name"] == "Test GPU"
        assert gpu_data["temperature"] == 65.0
        assert gpu_data["usagePercent"] == 80.0
        assert gpu_data["memoryUsed"] == 8000
        assert gpu_data["fanSpeed"] == 1500

        # Verify only GPU method was called
        mock_collector.collect_gpu_metrics.assert_called_once()
        mock_collector.collect_cpu_metrics.assert_not_called()

    @pytest.mark.asyncio
    async def test_memory_resolver(self, mock_collector):
        """Test memory resolver returns correct data."""

        # Create expected memory data with CORRECT field names
        expected_memory = MemoryMetrics(
            ram_used=8589934592,  # 8GB in bytes
            ram_total=17179869184,  # 16GB in bytes
            ram_percent=50.0,
            disk_used=107374182400,  # 100GB in bytes
            disk_total=214748364800,  # 200GB in bytes
            disk_percent=50.0,
        )
        mock_collector.collect_memory_metrics.return_value = expected_memory

        # Create mock GraphQL info object with collector in context
        mock_info = MagicMock()
        mock_info.context = {"collector": mock_collector}

        # Create query instance and call resolver
        query = Query()
        result = await query.memory(mock_info)

        assert result == expected_memory
        mock_collector.collect_memory_metrics.assert_called_once()


class TestGraphQLQueries:
    """Test complete GraphQL query scenarios."""

    def test_full_telemetry_query(self, client, mock_collector, mocker):
        """Test full telemetry query returns all data."""
        mocker.patch("app.agent.api.collector_instance", mock_collector)

        query = """
        query {
            telemetry {
                timestamp
                cpu { name, temperature }
                gpu { name, temperature }
                memory { ramPercent }
                network { interface, ipAddress }
                system { hostname, osName }
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200

        data = response.json()
        telemetry = data["data"]["telemetry"]

        assert telemetry["timestamp"] == 1704067200.0
        assert telemetry["cpu"]["name"] == "Test CPU"
        assert telemetry["gpu"]["name"] == "Test GPU"
        assert telemetry["system"]["hostname"] == "test-machine"
        assert len(telemetry["network"]) == 1

        # Verify full collection was called (not individual methods)
        mock_collector.collect_all_metrics.assert_called_once()

    def test_multiple_separate_fields(self, client, mock_collector, mocker):
        """Test query with multiple separate fields calls individual methods."""
        mocker.patch("app.agent.api.collector_instance", mock_collector)

        query = """
        query {
            cpu { temperature }
            memory { ramPercent }
            system { hostname }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["cpu"]["temperature"] == 45.0
        assert data["data"]["memory"]["ramPercent"] == 50.0
        assert data["data"]["system"]["hostname"] == "test-machine"

        # Verify individual methods were called (not full collection)
        mock_collector.collect_cpu_metrics.assert_called_once()
        mock_collector.collect_memory_metrics.assert_called_once()
        mock_collector.collect_system_metrics.assert_called_once()
        mock_collector.collect_all_metrics.assert_not_called()

    def test_health_query(self, client):
        """Test simple health query."""
        query = """
        query {
            health
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["health"] == "OK"


class TestGraphQLErrorHandling:
    """Test GraphQL error scenarios."""

    def test_invalid_field_query(self, client):
        """Test query with non-existent field returns error."""
        query = """
        query {
            nonExistentField {
                someData
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200  # GraphQL returns 200 with errors

        data = response.json()
        assert "errors" in data
        assert "nonExistentField" in str(data["errors"])

    @pytest.mark.asyncio
    async def test_malformed_query(self, client):
        """Test that malformed GraphQL queries return errors."""

        malformed_query = {
            "query": "{ invalid_field_that_does_not_exist }"  # Field doesn't exist in schema
        }

        response = client.post("/graphql", json=malformed_query)

        # GraphQL returns 200 but with errors in the response body
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data
        assert len(data["errors"]) > 0
