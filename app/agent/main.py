"""
Main application entry point for the telemetry agent.
"""

import argparse
import asyncio
import os
import signal
from typing import Any

import uvicorn
from dotenv import load_dotenv

from app.agent.api import app
from app.agent.telemetry import TelemetryCollector

load_dotenv()


async def console_mode() -> None:
    """Run the telemetry agent."""
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


def server_mode() -> None:
    """Run GraphQL API server mode."""
    tailscale_ip = os.getenv("TAILSCALE_IP", "127.0.0.1")
    port = int(os.getenv("BIND_PORT", "8000"))
    print("Starting System Telemetry Agent Server...")
    print("Configuration:")
    print(f"   • Tailscale IP: {tailscale_ip}")
    print(f"   • Port: {port}")
    print()
    print("GraphQL API endpoints:")
    print(f"   • GraphQL Playground: http://{tailscale_ip}:{port}/graphql")
    print(f"   • Health Check: http://{tailscale_ip}:{port}/health")
    print(f"   • API Docs: http://{tailscale_ip}:{port}/docs")
    print()
    print("Ready for remote polling via Tailscale")
    print("Press Ctrl+C to stop")

    uvicorn.run(
        app,
        host=tailscale_ip,
        port=port,
        reload=False,
        access_log=True,
    )


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

    args = parser.parse_args()

    try:
        if args.server:
            server_mode()
        else:
            asyncio.run(console_mode())
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()
