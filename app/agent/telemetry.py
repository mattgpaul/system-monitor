"""
Telemetry data collection module.

This module collects system metrics in a structured format
"""

import asyncio
import os
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil

# Force psutil evaluation
_ = psutil.cpu_count()  # This ensures psutil is fully loaded


class GPUVendor(Enum):
    """GPU Vendor IDs"""

    AMD = "0x1002"
    NVIDIA = "0x10de"
    INTEL = "0x8086"

    @classmethod
    def get_name(cls, vendor_id: str) -> str:
        """Get vendor name from ID."""
        for vendor in cls:
            if vendor.value == vendor_id:
                return vendor.name
        return f"Unknown Vendor ({vendor_id})"


@dataclass
class GPUDevice:
    """GPU Device information"""

    device_id: str
    name: str
    vendor: GPUVendor


# AMD GPU Database
AMD_DEVICES: Dict[str, str] = {
    "0x164e": "Radeon RX 7900 XTX",
    "0x164d": "Radeon RX 7900 XT",
    "0x164c": "Radeon RX 7900 GRE",
    "0x15dd": "Radeon RX 6900 XT",
    "0x15dc": "Radeon RX 6800 XT",
    "0x15db": "Radeon RX 6800",
    "0x1638": "Radeon RX 6700 XT",
    "0x163f": "Radeon RX 6700",
    "0x1681": "Radeon RX 6600 XT",
    "0x1679": "Radeon RX 6600",
}

# NVIDIA GPU Database
NVIDIA_DEVICES: Dict[str, str] = {
    "0x2684": "GeForce RTX 4090",
    "0x2682": "GeForce RTX 4080",
    "0x2704": "GeForce RTX 4070 Ti",
    "0x2783": "GeForce RTX 4070",
    "0x2544": "GeForce RTX 3060",
    "0x220a": "GeForce RTX 3080",
    "0x2206": "GeForce RTX 3080 Ti",
    "0x2208": "GeForce RTX 3070 Ti",
    "0x2204": "GeForce RTX 3070",
}


@dataclass
class CPUMetrics:
    """CPU telmetry data."""

    name: str
    temperature: Optional[float]  # Celsius
    usage_percent: float
    core_usage: List[float]  # Per-core usage percentages
    frequency: float  # MHz


@dataclass
class GPUMetrics:
    """GPU telemetry data."""

    name: str
    temperature: Optional[float]  # Celsius
    usage_percent: Optional[float]  # Celsius
    memory_used: Optional[int]  # MB
    memory_total: Optional[int]  # MB
    fan_speed: Optional[int]  # RPM
    clock_speed: Optional[str]  # MHz


@dataclass
class MemoryMetrics:
    """Memory telemetry data."""

    ram_used: int  # Bytes
    ram_total: int
    ram_percent: float
    disk_used: int
    disk_total: int
    disk_percent: float


@dataclass
class NetworkMetrics:
    """Network telemetry data."""

    interface: str
    ip_address: Optional[str]
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    speed_upload: float  # Bytes/sec
    speed_download: float  # Bytes/sec


@dataclass
class SystemMetrics:
    """System information"""

    hostname: str
    os_name: str
    kernel_version: str
    uptime_seconds: int
    user: str
    boot_time: float


@dataclass
class TelemetryData:
    """Complete telemetry data structure"""

    timestamp: float
    cpu: CPUMetrics
    gpu: Optional[GPUMetrics]
    memory: MemoryMetrics
    network: List[NetworkMetrics]
    system: SystemMetrics


class TelemetryCollector:
    """Collects system telemetry data."""

    def __init__(self) -> None:
        self.previous_network_stats: Dict[str, Dict] = {}
        self.previous_time = time.time()

        # Static data cache
        self._static_cache: Dict[str, Any] = {
            "cpu_name": None,
            "cpu_core_count": None,
            "gpu_name": None,
            "gpu_total_vram": None,
            "total_ram": None,
            "total_disk": None,
            "hostname": None,
            "os_name": None,
            "kernel_version": None,
            "boot_time": None,
        }

    async def _ensure_cache_initialized(self) -> None:
        """Ensure static cache is initialized."""
        if self._static_cache["cpu_name"] is None:
            await self._cache_static_data()

    async def _cache_static_data(self) -> None:
        """Cach all static system information at once."""
        try:
            # CPU static data
            self._static_cache["cpu_name"] = await self._get_cpu_name_static()
            self._static_cache["cpu_core_count"] = psutil.cpu_count()

            # GPU static data
            self._static_cache["gpu_name"] = await self._get_gpu_name_static()
            self._static_cache["gpu_total_vram"] = await self._get_gpu_total_vram()

            # Memory static data
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            self._static_cache["total_ram"] = memory.total
            self._static_cache["total_disk"] = disk.total

            # System static data
            self._static_cache["hostname"] = os.uname().nodename
            self._static_cache["os_name"] = await self._get_os_name_static()
            self._static_cache["kernel_version"] = os.uname().release
            self._static_cache["boot_time"] = psutil.boot_time()

        except Exception as e:
            print(f"Warning: Failed to cache static data: {e}")

    async def _get_cpu_name_static(self) -> str:
        """Get CPU name (cached)."""
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("model name"):
                        cpu_name = line.split(":", 1)[1].strip()
                        return cpu_name.replace(" 8-Core Processor", "")
            return "Unknown CPU"
        except Exception:
            return "Unkown CPU"

    async def _get_gpu_name_static(self) -> str:
        """Get GPU name (cached)."""
        return await self._get_gpu_name_from_device_ids()

    async def _get_gpu_total_vram(self) -> Optional[int]:
        """Get total GPU VRAM (cached)."""
        try:
            with open("/sys/class/drm/card0/device/mem_info_vram_total", "r") as f:
                vram_bytes = int(f.read().strip())
                return vram_bytes // (1024 * 1024)
        except (FileNotFoundError, PermissionError, ValueError, OSError):
            return 24560

    async def _get_os_name_static(self) -> str:
        """Get OS name (cached version)."""
        return self._get_os_name()

    async def collect_memory_metrics(self) -> MemoryMetrics:
        """Collect memory telemetry data."""
        # RAM metrics (use cached total)
        memory = psutil.virtual_memory()
        total_ram = self._static_cache.get("total_ram") or memory.total

        # Disk metrics (use cached total)
        disk = psutil.disk_usage("/")
        total_disk = self._static_cache.get("total_disk") or disk.total

        return MemoryMetrics(
            ram_used=memory.used,
            ram_total=total_ram,
            ram_percent=memory.percent,
            disk_used=disk.used,
            disk_total=total_disk,
            disk_percent=(disk.used / total_disk) * 100,
        )

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system information"""
        return SystemMetrics(
            hostname=self._static_cache.get("hostname") or os.uname().nodename,
            os_name=self._static_cache.get("os_name") or self._get_os_name(),
            kernel_version=self._static_cache.get("kernel_version") or os.uname().release,
            uptime_seconds=int(
                time.time() - (self._static_cache.get("boot_time") or psutil.boot_time())
            ),
            user=os.getlogin(),  # This changes if user switches, so don't cache
            boot_time=self._static_cache.get("boot_time") or psutil.boot_time(),
        )

    def _get_os_name(self) -> str:
        """Get OS name using lsb-release."""
        try:
            result = subprocess.run(
                ["lsb_release", "-d"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                return result.stdout.split("\t")[1].strip()

            return "Unknown OS"

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return "Exception: OS subprocess command did not execute properly"

    async def collect_network_metrics(self) -> List[NetworkMetrics]:
        """Collect network telemetry data."""
        network_interfaces = []
        current_time = time.time()
        time_delta = current_time - self.previous_time

        # Get network interface stats
        net_stats = psutil.net_io_counters(pernic=True)

        for interface_name, stats in net_stats.items():
            # Skip loopback interface
            if interface_name == "lo":
                continue

            # Get IP address
            ip_address = self._get_interface_ip(interface_name)

            # Calculate speeds
            speed_upload = 0.0
            speed_download = 0.0

            if interface_name in self.previous_network_stats and time_delta > 0:
                prev_stats = self.previous_network_stats[interface_name]
                speed_upload = (stats.bytes_sent - prev_stats["bytes_sent"]) / time_delta
                speed_download = (stats.bytes_recv - prev_stats["bytes_recv"]) / time_delta

            # Store current stats for next calculation
            self.previous_network_stats[interface_name] = {
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
            }

            network_interfaces.append(
                NetworkMetrics(
                    interface=interface_name,
                    ip_address=ip_address,
                    bytes_sent=stats.bytes_sent,
                    bytes_received=stats.bytes_recv,
                    packets_sent=stats.packets_sent,
                    packets_received=stats.packets_recv,
                    speed_upload=speed_upload,
                    speed_download=speed_download,
                )
            )

        self.previous_time = current_time
        return network_interfaces

    def _get_interface_ip(self, interface_name: str) -> Optional[str]:
        """Get IP address for network interface."""
        try:
            addresses = psutil.net_if_addrs()
            if interface_name in addresses:
                for addr in addresses[interface_name]:
                    if addr.family == 2:  # IPv4
                        return addr.address
            return None
        except Exception:
            return None

    async def collect_cpu_metrics(self) -> CPUMetrics:
        """Collect CPU telemetry data."""
        try:
            # Use cached CPU name if available
            cpu_name = self._static_cache.get("cpu_name") or await self._get_cpu_name_static()

            # Dynamic data (collect fresh each time)
            temperature = await self._get_cpu_temperature()
            cpu_percent = psutil.cpu_percent(interval=1)
            core_usage = psutil.cpu_percent(interval=1, percpu=True)

            cpu_freq = psutil.cpu_freq()
            frequency = cpu_freq.current if cpu_freq else 0.0

            return CPUMetrics(
                name=cpu_name,
                temperature=temperature,
                usage_percent=cpu_percent,
                core_usage=core_usage,
                frequency=frequency,
            )
        except Exception:
            return CPUMetrics(
                name="Unknown",
                temperature=None,
                usage_percent=0.0,
                core_usage=[],
                frequency=0.0,
            )

    async def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature by reading system files directly."""
        try:
            # Common AMD Ryzen temperature file locations
            temp_files = [
                "/sys/class/hwmon/hwmon0/temp1_input",
                "/sys/class/hwmon/hwmon1/temp1_input",
                "/sys/class/hwmon/hwmon2/temp1_input",
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/thermal/thermal_zone1/temp",
            ]

            for temp_file in temp_files:
                try:
                    with open(temp_file, "r") as f:
                        # Temperature is in millidegrees Celsius
                        temp_raw = int(f.read().strip())
                        temp_celsius = temp_raw / 1000.0

                        # Sanity check
                        if 0 <= temp_celsius <= 120:
                            return temp_celsius
                except (FileNotFoundError, ValueError, PermissionError):
                    continue

            return None

        except Exception:
            return None

    async def collect_gpu_metrics(self) -> Optional[GPUMetrics]:
        """Collect GPU telemetry data using direct file reading."""
        try:
            # Use cached GPU name and total VRAM
            gpu_name = self._static_cache.get("gpu_name", "Unknown GPU")
            total_vram = self._static_cache.get("gpu_total_vram") or 24560

            # Get dynamic GPU metrics
            gpu_data = await self._get_amdgpu_metrics()

            if gpu_data:
                return GPUMetrics(
                    name=gpu_name,
                    temperature=gpu_data.get("temperature"),
                    usage_percent=gpu_data.get("usage"),
                    memory_used=gpu_data.get("vram_used"),
                    memory_total=total_vram,
                    fan_speed=gpu_data.get("fan_speed"),
                    clock_speed=gpu_data.get("clock_speed"),
                )

            return None
        except Exception:
            return None

    async def _get_gpu_name_from_device_ids(self) -> str:
        """Get GPU name from vendor/device ID files."""
        try:
            # Read vendor and device IDs
            vendor_id = None
            device_id = None

            try:
                with open("/sys/class/drm/card0/device/vendor", "r") as f:
                    vendor_id = f.read().strip()
            except (FileNotFoundError, PermissionError):
                pass

            try:
                with open("/sys/class/drm/card0/device/device", "r") as f:
                    device_id = f.read().strip()
            except (FileNotFoundError, PermissionError):
                pass

            # Lookup GPU name using enum and device database
            if vendor_id and device_id:
                vendor_name = GPUVendor.get_name(vendor_id)

                # Look up device name based on vendor
                if vendor_id == GPUVendor.AMD.value and device_id in AMD_DEVICES:
                    return f"AMD {AMD_DEVICES[device_id]}"
                elif vendor_id == GPUVendor.NVIDIA.value and device_id in NVIDIA_DEVICES:
                    return f"NVIDIA {NVIDIA_DEVICES[device_id]}"
                else:
                    # Return vendor name with device ID if not in database
                    return f"{vendor_name} GPU (Device: {device_id})"

            return "Unknown GPU"

        except Exception:
            return "Unknown GPU"

    async def _get_amdgpu_metrics(self) -> Optional[Dict]:
        """Get AMD GPU metrics by reading sysfs files directly."""
        try:
            gpu_data = {}
            base_path = "/sys/class/drm/card0/device"

            # GPU temperature
            temp_files = [
                f"{base_path}/hwmon/hwmon2/temp1_input",
                f"{base_path}/hwmon/hwmon3/temp1_input",
                f"{base_path}/hwmon/hwmon4/temp1_input",
            ]

            for temp_file in temp_files:
                try:
                    with open(temp_file, "r") as f:
                        temp_raw = int(f.read().strip())
                        temp_celsius = temp_raw / 1000.0
                        if 0 <= temp_celsius <= 120:
                            gpu_data["temperature"] = temp_celsius
                            break
                except (FileNotFoundError, ValueError, PermissionError):
                    continue

            # GPU usage percentage
            try:
                with open(f"{base_path}/gpu_busy_percent", "r") as f:
                    gpu_data["usage"] = float(f.read().strip())
            except (FileNotFoundError, ValueError, PermissionError):
                pass

            # VRAM usage
            try:
                with open(f"{base_path}/mem_info_vram_used", "r") as f:
                    vram_used_bytes = int(f.read().strip())
                    gpu_data["vram_used"] = vram_used_bytes // (1024 * 1024)  # Convert to MB
            except (FileNotFoundError, ValueError, PermissionError):
                pass

            # Fan speed
            fan_files = [
                f"{base_path}/hwmon/hwmon2/fan1_input",
                f"{base_path}/hwmon/hwmon3/fan1_input",
                f"{base_path}/hwmon/hwmon4/fan1_input",
            ]

            for fan_file in fan_files:
                try:
                    with open(fan_file, "r") as f:
                        gpu_data["fan_speed"] = int(f.read().strip())
                        break
                except (FileNotFoundError, ValueError, PermissionError):
                    continue

            # GPU clock speed
            try:
                with open(f"{base_path}/pp_dpm_sclk", "r") as f:
                    for line in f:
                        if "*" in line:  # Current clock speed marked with *
                            clock_speed = line.split()[1]
                            gpu_data["clock_speed"] = clock_speed
                            break
            except (FileNotFoundError, ValueError, PermissionError):
                pass

            return gpu_data if gpu_data else None

        except Exception:
            return None

    async def collect_all_metrics(self) -> TelemetryData:
        """Collect all telemetry data concurrently."""
        # Ensure cache is initialized
        await self._ensure_cache_initialized()

        timestamp = time.time()

        # Create tasks for all metric collection (run concurrently)
        cpu_task = asyncio.create_task(self.collect_cpu_metrics())
        gpu_task = asyncio.create_task(self.collect_gpu_metrics())
        memory_task = asyncio.create_task(self.collect_memory_metrics())
        network_task = asyncio.create_task(self.collect_network_metrics())
        system_task = asyncio.create_task(self.collect_system_metrics())

        # Wait for all tasks to complete
        cpu_metrics = await cpu_task
        gpu_metrics = await gpu_task
        memory_metrics = await memory_task
        network_metrics = await network_task
        system_metrics = await system_task

        return TelemetryData(
            timestamp=timestamp,
            cpu=cpu_metrics,
            gpu=gpu_metrics,
            memory=memory_metrics,
            network=network_metrics,
            system=system_metrics,
        )
