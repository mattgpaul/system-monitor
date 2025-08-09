import logging

import httpx
from celery import shared_task
from django.conf import settings

from .graphql_queries import get_query

logger = logging.getLogger(__name__)


@shared_task
def poll_agent_telemetry():
    """
    Poll the agent for current telemetry data via GraphQL.
    This task runs every second (1Hz) to collect system metrics.
    """
    agent_url = f"{settings.AGENT_BASE_URL}/graphql"
    timeout = settings.AGENT_TIMEOUT

    try:
        # Get the basic telemetry query from our .graphql files
        query = get_query("basic")  # Uses telemetry_basic.graphql

        logger.info(f"Polling agent at {agent_url}")

        # Make GraphQL request to agent
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                agent_url, json={"query": query}, headers={"Content-Type": "application/json"}
            )

        if response.status_code == 200:
            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return {"status": "error", "message": "GraphQL errors"}

            # Extract telemetry data
            telemetry = data.get("data", {}).get("telemetry", {})

            if telemetry:
                hostname = telemetry.get("system", {}).get("hostname", "unknown")
                logger.info(f"Received telemetry from {hostname}")

                # TODO: Store telemetry data in database
                # For now, just log it
                logger.info(f"CPU: {telemetry.get('cpu', {})}")
                logger.info(f"Memory: {telemetry.get('memory', {})}")

                return {
                    "status": "success",
                    "hostname": hostname,
                    "timestamp": telemetry.get("timestamp"),
                    "data_received": True,
                }
            else:
                logger.warning("No telemetry data in response")
                return {"status": "warning", "message": "No telemetry data"}

        else:
            logger.error(f"HTTP error {response.status_code}: {response.text}")
            return {"status": "error", "message": f"HTTP {response.status_code}"}

    except httpx.TimeoutException:
        logger.warning(f"Agent timeout after {timeout} seconds - agent may be offline")
        return {"status": "timeout", "message": "Agent offline or unreachable"}

    except Exception as e:
        logger.error(f"Unexpected error polling agent: {e}")
        return {"status": "error", "message": str(e)}
