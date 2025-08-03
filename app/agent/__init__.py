"""
Agent package for collecting system telemetry data.

This package contains the REST API server that exposes system metrics
for remote monitoring.
"""

from typing import Any, Dict

# Agent version - could be different from the main package if needed
__version__ = "0.1.0"

# Default configuration values
DEFAULT_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "update_interval": 1.0,  # seconds
    "metrics_enabled": {
        "cpu": True,
        "memory": True,
        "disk": True,
        "network": True,
        "gpu": True,
    },
}


def get_agent_info() -> Dict[str, Any]:
    """
    Get basic information about the agent.

    Returns:
        Dict containing agent version and configuration
    """
    return {
        "version": __version__,
        "config": DEFAULT_CONFIG,
    }
