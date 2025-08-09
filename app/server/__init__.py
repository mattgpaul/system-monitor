"""
Container package for monitoring system telemetry data.

This package contains the Django application that collects, stores,
and visualizes system metrics from remote agents.
"""

from typing import Any, Dict, List

# Container version
__version__ = "0.1.0"

# Default configuration for the monitoring container
DEFAULT_CONFIG = {
    "django": {
        "debug": False,
        "allowed_hosts": ["*"],
        "secret_key": "change-this-in-prod",
    },
    "polling": {
        "interval": 5.0,  # seconds between agent polls
        "timeout": 10.0,  # seconds before request timeout
        "retry_attempts": 3,
    },
    "agents": {
        "endpoints": [
            # Will be populated from config file
            # 'http://192.168.1.100:8000'
        ]
    },
    "influxdb": {
        "host": "localhost",
        "port": 8086,
        "database": "system_metrics",
        "retention_policy": "30d",
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
    },
    "grafana": {
        "host": "localhost",
        "port": 3000,
        "admin_user": "admin",
        "admin_password": "admin",
    },
}


def get_container_info() -> Dict[str, Any]:
    """
    Get basic information about the container.

    Returns:
        Dict containing container version and configuration
    """
    return {
        "version": __version__,
        "config": DEFAULT_CONFIG,
    }


def get_agent_endpoints() -> List[str]:
    """
    Get the list of agent endpoints from the configuration.

    Returns:
        List of agent endpoints
    """
    return DEFAULT_CONFIG["agents"]["endpoints"]
