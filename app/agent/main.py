"""
Main application entry point for the telemetry agent.
Pure environment variable configuration following 12-factor app principles.
"""

import argparse
import asyncio
import logging
import os
import signal
from pathlib import Path
from typing import Any

import uvicorn

from app.agent.api import app
from app.agent.telemetry import TelemetryCollector
from app.core.logging_config import setup_logging

logger = logging.getLogger("telemetry_agent.main")


async def console_mode(log_level: str = "INFO") -> None:
    """Run console mode with live telemetry display."""
    setup_logging(level=log_level)

    collector = TelemetryCollector()

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum: int, frame: Any) -> None:
        print("\nShutdown signal received. Exiting...")
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting telemetry collection in console mode")
    print("System Telemetry Agent - Console Mode")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print()

    try:
        while True:
            try:
                telemetry_data = await collector.collect_all()

                # Clear screen and display updated telemetry
                os.system("clear" if os.name == "posix" else "cls")
                print("System Telemetry Agent - Live Display")
                print("=" * 50)
                print(f"Timestamp: {telemetry_data.timestamp}")
                print(f"Hostname: {telemetry_data.system.hostname}")
                print()

                print("CPU Information:")
                print(f"  Name: {telemetry_data.cpu.name}")
                print(f"  Usage: {telemetry_data.cpu.usage_percent:.1f}%")
                print(f"  Frequency: {telemetry_data.cpu.frequency} MHz")
                if telemetry_data.cpu.temperature:
                    print(f"  Temperature: {telemetry_data.cpu.temperature}°C")
                print()

                print("Memory Information:")
                print(f"  RAM Used: {telemetry_data.memory.ram_used:.1f} GB")
                print(f"  RAM Total: {telemetry_data.memory.ram_total:.1f} GB")
                print(f"  RAM Usage: {telemetry_data.memory.ram_percent:.1f}%")
                print()

                if telemetry_data.gpu:
                    print("GPU Information:")
                    print(f"  Name: {telemetry_data.gpu.name}")
                    print(f"  Usage: {telemetry_data.gpu.usage_percent}%")
                    print(f"  Memory: {telemetry_data.gpu.memory_used}/{telemetry_data.gpu.memory_total} MB")
                    if telemetry_data.gpu.temperature:
                        print(f"  Temperature: {telemetry_data.gpu.temperature}°C")
                    print()

                print("Press Ctrl+C to stop")

                # Wait 1 second before next update
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error collecting telemetry: {e}")
                await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Console mode shutdown requested by user")
        print("\nExiting console mode...")


def server_mode(log_level: str = "INFO") -> None:
    """Run GraphQL API server mode."""
    setup_logging(level=log_level)

    # Environment variable configuration with sensible defaults
    agent_host = os.getenv("AGENT_HOST", "127.0.0.1")
    agent_port = int(os.getenv("AGENT_PORT", "8000"))

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
