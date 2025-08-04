"""
GraphQL schema for the telemetry agent.

This module defines the GraphQL queries that clients can use
to fetch telemetry data from the system.
"""

import strawberry
import logging
from typing import Optional, List
from strawberry.types import Info

logger = logging.getLogger("telemetry_agent.schema")

from app.agent.telemetry import (
    CPUMetrics,
    GPUMetrics,
    MemoryMetrics,
    NetworkMetrics,
    SystemMetrics,
    TelemetryCollector,
    TelemetryData,
)


@strawberry.type
class Query:
    """Root GraphQL query type."""

    @strawberry.field
    async def telemetry(self, info: Info) -> TelemetryData:
        """
        Get complete system telemetry data.

        Returns all available metrics: CPU, GPU, memory, network, and system info.
        """
        logger.info("GraphQL query: complete telemetry requested")
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_all_metrics()

    @strawberry.field
    async def cpu(self, info: Info) -> CPUMetrics:
        """Get only CPU metrics."""
        logger.info("GraphQL query: CPU metrics requested")
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_cpu_metrics()

    @strawberry.field
    async def gpu(self, info: Info) -> Optional[GPUMetrics]:
        """Get only GPU metrics (may be None if no GPU detected)."""
        logger.info("GraphQL query: GPU metrics requested")
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_gpu_metrics()

    @strawberry.field
    async def memory(self, info: Info) -> MemoryMetrics:
        """Get only memory and disk metrics."""
        logger.info("GraphQL query: memory metrics requested")
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_memory_metrics()

    @strawberry.field
    async def network(self, info: Info) -> List[NetworkMetrics]:
        """Get network interface metrics."""
        logger.info("GraphQL query: network metrics requested")
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_network_metrics()

    @strawberry.field
    async def system(self, info: Info) -> SystemMetrics:
        """Get system information."""
        logger.info("GraphQL query: system metrics requested")
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_system_metrics()

    @strawberry.field
    async def health(self) -> str:
        """Simple health check endpoint."""
        return "OK"


# Create the schema
schema = strawberry.Schema(query=Query)
