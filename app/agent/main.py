"""
Main application entry point for the telemetry agent.
"""

import asyncio
import signal
from typing import Any

from app.agent.telemetry import TelemetryCollector


async def main() -> None:
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
            cpu_temp = (
                f"{data.cpu.temperature:.1f}°C" if data.cpu.temperature else "N/A"
            )
            gpu_temp = (
                f"{data.gpu.temperature:.1f}°C"
                if data.gpu and data.gpu.temperature
                else "N/A"
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
