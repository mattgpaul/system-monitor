"""
Main application entry point for the telemetry agent.
"""

import argparse
import asyncio
import logging
import os
import signal
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv

from app.agent.api import app
from app.agent.telemetry import TelemetryCollector
from app.core.logging_config import setup_logging

logger = logging.getLogger("telemetry_agent.main")


# Load environment variables from dev.env or prod.env (same as server)
def load_environment() -> None:
    """Load environment variables using the same logic as the server."""
    # Get the project root (three levels up from this file)
    project_root = Path(__file__).resolve().parent.parent.parent

    # Load environment variables from dev.env or prod.env
    env_type = os.getenv("ENV", "dev")
    env_file = project_root / f"{env_type}.env"

    if env_file.exists():
        load_dotenv(env_file)
        print(f"Agent loaded environment from {env_file}")
    else:
        # Fallback to .env file if it exists
        fallback_env = project_root / ".env"
        if fallback_env.exists():
            load_dotenv(fallback_env)
            print(f"Agent loaded fallback environment from {fallback_env}")
        else:
            print("Agent: No environment file found, using defaults")


# Load environment at module import
load_environment()


async def console_mode(log_level: str = "INFO") -> None:
    """Run the telemetry agent."""
    setup_logging(level=log_level)
    collector = await TelemetryCollector.create()
    running = True

    def signal_handler(signum: int, frame: Any) -> None:
        nonlocal running
        print(f"\nReceived signal {signum}, shutting down...")
        running = False

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Starting telemetry collection...")
    print("Press Ctrl+C to stop")

    while running:
        try:
            # Use the collector
            data = await collector.collect_all_metrics()

            # Simple display of key metrics
            cpu_temp = f"{data.cpu.temperature:.1f}°C" if data.cpu.temperature else "N/A"
            gpu_temp = (
                f"{data.gpu.temperature:.1f}°C" if data.gpu and data.gpu.temperature else "N/A"
            )

            print(
                f"CPU: {cpu_temp} ({data.cpu.usage_percent:.1f}%) | "
                f"GPU: {gpu_temp} | "
                f"RAM: {data.memory.ram_percent:.1f}% | "
                f"Disk: {data.memory.disk_percent:.1f}%"
            )

            await asyncio.sleep(1)

        except KeyboardInterrupt:
            running = False
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)

    print("Shutdown complete.")


def server_mode(log_level: str = "INFO") -> None:
    """Run GraphQL API server mode."""

    setup_logging(level=log_level)

    # Network-agnostic configuration
    agent_host = os.getenv("AGENT_HOST", os.getenv("TAILSCALE_IP", "127.0.0.1"))
    agent_port = int(os.getenv("AGENT_PORT", os.getenv("BIND_PORT", "8000")))

    logger.info("Starting System Telemetry Agent Server")
    logger.info("Configuration: Host=%s, Port=%d", agent_host, agent_port)

    print("Starting System Telemetry Agent Server...")
    print("Configuration:")
    print(f"   • Host: {agent_host}")
    print(f"   • Port: {agent_port}")
    print()
    print("GraphQL API endpoints:")
    print(f"   • GraphQL Playground: http://{agent_host}:{agent_port}/graphql")
    print(f"   • Health Check: http://{agent_host}:{agent_port}/health")
    print(f"   • API Docs: http://{agent_host}:{agent_port}/docs")
    print()
    print("Ready for remote polling")
    print("Press Ctrl+C to stop")

    try:
        uvicorn.run(
            app,
            host=agent_host,
            port=agent_port,
            reload=False,
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error("Server failed to start: %s", str(e))
        raise


def main() -> None:
    """Main entry point with mode selection."""
    parser = argparse.ArgumentParser(
        description="System Telemetry Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
  python -m app.agent.main                    # Console mode (default)
  python -m app.agent.main --console          # Console mode (explicit)
  python -m app.agent.main --server           # Server mode for remote polling
        """,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--console",
        action="store_true",
        default=True,
        help="Run in console mode with live telemetry display (default)",
    )
    group.add_argument(
        "--server", action="store_true", help="Run GraphQL API server for remote polling"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    args = parser.parse_args()

    try:
        if args.server:
            server_mode(log_level=args.log_level)
        else:
            asyncio.run(console_mode(log_level=args.log_level))
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()
