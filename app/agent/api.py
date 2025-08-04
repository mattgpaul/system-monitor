"""
FastAPI application for the telemetry agent.

This module creates the FastAPI app with GraphQL endpoint
for serving system telemetry data.
"""

from typing import Any, Dict

from fastapi import FastAPI, Request
from strawberry.fastapi import GraphQLRouter

from app.agent import __version__
from app.agent.schema import schema
from app.agent.telemetry import TelemetryCollector

collector_instance = TelemetryCollector()


async def get_context(request: Request) -> Dict[str, Any]:
    """Provide context for GraphQL resolvers."""
    return {"collector": collector_instance}


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
