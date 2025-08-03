"""
GraphQL schema for the telemetry agent.

This module defines the GraphQL queries that clients can use
to fetch telemetry data from the system.
"""

from typing import List, Optional

import strawberry
from strawberry.types import Info

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
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_all_metrics()

    @strawberry.field
    async def cpu(self, info: Info) -> CPUMetrics:
        """Get only CPU metrics."""
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_cpu_metrics()

    @strawberry.field
    async def gpu(self, info: Info) -> Optional[GPUMetrics]:
        """Get only GPU metrics (may be None if no GPU detected)."""
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_gpu_metrics()

    @strawberry.field
    async def memory(self, info: Info) -> MemoryMetrics:
        """Get only memory and disk metrics."""
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_memory_metrics()

    @strawberry.field
    async def network(self, info: Info) -> List[NetworkMetrics]:
        """Get network interface metrics."""
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_network_metrics()

    @strawberry.field
    async def system(self, info: Info) -> SystemMetrics:
        """Get system information."""
        collector: TelemetryCollector = info.context["collector"]
        return await collector.collect_system_metrics()

    @strawberry.field
    async def health(self) -> str:
        """Simple health check endpoint."""
        return "OK"


# Create the schema
schema = strawberry.Schema(query=Query)
