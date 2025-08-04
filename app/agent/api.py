"""
FastAPI application for the telemetry agent.

This module creates the FastAPI app with GraphQL endpoint
for serving system telemetry data.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from strawberry.fastapi import GraphQLRouter

from app.agent import __version__
from app.agent.schema import schema
from app.agent.telemetry import TelemetryCollector

logger = logging.getLogger("telemetry_agent.api")

collector_instance: Optional[TelemetryCollector] = None


async def get_collector() -> TelemetryCollector:
    """Get or create the global collector instance using lazy initialization."""
    global collector_instance
    if collector_instance is None:
        logger.info("Initializing telemetry collector for first GraphQL request")
        collector_instance = await TelemetryCollector.create()
        logger.info("Collector ready for GraphQL requests")
    return collector_instance


async def get_context(request: Request) -> Dict[str, Any]:
    """Provide context for GraphQL resolvers."""
    collector = await get_collector()
    return {"collector": collector}


app = FastAPI(
    title="System Telemetry Agent",
    description="GraphQL API for system monitoring and telemetry data collection",
    version=__version__,
)

# Add GraphQL endpoint with collector context
graphql_app = GraphQLRouter(schema, context_getter=get_context)  # type: ignore[arg-type]
app.include_router(graphql_app, prefix="/graphql")


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "OK", "version": __version__}


# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "System Telemetry Agent",
        "version": __version__,
        "graphql_endpoint": "/graphql",
        "health_endpoint": "/health",
        "documentation": "/docs",
    }
