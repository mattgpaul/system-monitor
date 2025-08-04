"""
Main application entry point for the telemetry agent.
"""

import argparse
import asyncio
import signal
import uvicorn
from typing import Any

from app.agent.telemetry import TelemetryCollector
from app.agent.api import app


async def console_mode() -> None:
    """Run the telemetry agent."""
    collector = TelemetryCollector()
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
    print("Starting System Telemetry Agent Server...")
    print("GraphQL API endpoints:")
    print("   • GraphQL Playground: http://localhost:8000/graphql")
    print("   • Health Check: http://localhost:8000/health")
    print("   • API Docs: http://localhost:8000/docs")
    print("\nReady for remote polling via Tailscale")
    print("Press Ctrl+C to stop")   

    uvicorn.run(
        app,
        host="0.0.0.0",  # Listen on all interfaces (including Tailscale)
        port=8000,
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
        """
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--console",
        action="store_true",
        default=True,
        help="Run in console mode with live telemetry display (default)"
    )
    group.add_argument(
        "--server",
        action="store_true",
        help="Run GraphQL API server for remote polling"
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
