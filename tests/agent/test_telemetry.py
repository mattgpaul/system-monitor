import pytest

from app.agent.telemetry import (
    CPUMetrics,
    GPUMetrics,
    GPUVendor,
    MemoryMetrics,
    NetworkMetrics,
    SystemMetrics,
    TelemetryCollector,
)


class TestGPUVendor:
    """Test cases for GPUVendor enum."""

    def test_vendor_values(self):
        """Test that the vendor IDs are correct."""
        assert GPUVendor.AMD.value == "0x1002"
        assert GPUVendor.NVIDIA.value == "0x10de"
        assert GPUVendor.INTEL.value == "0x8086"

    def test_get_name_known_vendor(self):
        """Test getting vendor name for known vendor."""
        assert GPUVendor.get_name("0x1002") == "AMD"
        assert GPUVendor.get_name("0x10de") == "NVIDIA"
        assert GPUVendor.get_name("0x8086") == "INTEL"

    def test_get_name_unknown_vendor(self):
        """Test getting vendor name for unknown vendor."""
        result = GPUVendor.get_name("0x9999")
        assert result == "Unknown Vendor (0x9999)"


class TestCPUMetrics:
    """Test cases for CPUMetrics dataclass."""

    def test_cpu_metrics_creation(self):
        """Test that CPUMetrics can be created with all fields."""
        cpu = CPUMetrics(
            name="AMD Ryzen 7 7800X3D",
            temperature=45.0,
            usage_percent=25.5,
            core_usage=[20.0, 30.0, 25.0, 15.0],
            frequency=3400.0,
        )
        assert cpu.name == "AMD Ryzen 7 7800X3D"
        assert cpu.temperature == 45.0
        assert cpu.usage_percent == 25.5
        assert len(cpu.core_usage) == 4
        assert cpu.frequency == 3400.0


class TestGPUMetrics:
    """Test cases for GPUMetrics dataclass."""

    def test_gpu_metrics_creation_all_fields(self):
        """Test GPUMetrics creation with all fields populated."""
        gpu = GPUMetrics(
            name="AMD Radeon RX 7900 XTX",
            temperature=65.0,
            usage_percent=80.0,
            memory_used=8000,
            memory_total=24000,
            fan_speed=1500,
            clock_speed="2100",
        )
        assert gpu.name == "AMD Radeon RX 7900 XTX"
        assert gpu.temperature == 65.0
        assert gpu.usage_percent == 80.0
        assert gpu.memory_used == 8000
        assert gpu.memory_total == 24000
        assert gpu.fan_speed == 1500
        assert gpu.clock_speed == "2100"

    def test_gpu_metrics_partial_fields(self):
        """Test GPUMetrics with some fields present, others None."""
        gpu = GPUMetrics(
            name="Partial GPU",
            temperature=70.0,  # Available
            usage_percent=None,  # Not available
            memory_used=4000,  # Available
            memory_total=None,  # Not available
            fan_speed=1200,  # Available
            clock_speed=None,  # Not available
        )
        assert gpu.temperature == 70.0
        assert gpu.usage_percent is None
        assert gpu.memory_used == 4000
        assert gpu.memory_total is None


class TestMemoryMetrics:
    """Test cases for MemoryMetrics dataclass."""

    def test_memory_metrics_creation(self):
        """Test MemoryMetrics creation with typical values."""
        memory = MemoryMetrics(
            ram_used=16000000000,  # 16GB in bytes
            ram_total=32000000000,  # 32GB in bytes
            ram_percent=50.0,  # 50% usage
            disk_used=500000000000,  # 500GB in bytes
            disk_total=1000000000000,  # 1TB in bytes
            disk_percent=50.0,  # 50% usage
        )
        assert memory.ram_used == 16000000000
        assert memory.ram_total == 32000000000
        assert memory.ram_percent == 50.0
        assert memory.disk_used == 500000000000
        assert memory.disk_total == 1000000000000
        assert memory.disk_percent == 50.0

    def test_memory_metrics_edge_cases(self):
        """Test MemoryMetrics with edge case values."""
        memory = MemoryMetrics(
            ram_used=0,  # Empty RAM (theoretical)
            ram_total=1000000,  # Small system
            ram_percent=0.0,  # 0% usage
            disk_used=1000000000000,  # Full disk
            disk_total=1000000000000,  # Same as used = 100%
            disk_percent=100.0,  # 100% usage
        )
        assert memory.ram_percent == 0.0
        assert memory.disk_percent == 100.0
        assert memory.ram_used == 0
        assert memory.disk_used == memory.disk_total


class TestNetworkMetrics:
    """Test cases for NetworkMetrics dataclass."""

    def test_network_metrics_active_interface(self):
        """Test NetworkMetrics for an active interface."""
        network = NetworkMetrics(
            interface="eth0",
            ip_address="192.168.1.100",
            bytes_sent=1000000,
            bytes_received=2000000,
            packets_sent=500,
            packets_received=800,
            speed_upload=1024.0,  # 1KB/s upload
            speed_download=2048.0,  # 2KB/s download
        )
        assert network.interface == "eth0"
        assert network.ip_address == "192.168.1.100"
        assert network.bytes_sent == 1000000
        assert network.bytes_received == 2000000
        assert network.packets_sent == 500
        assert network.packets_received == 800
        assert network.speed_upload == 1024.0
        assert network.speed_download == 2048.0

    def test_network_metrics_inactive_interface(self):
        """Test NetworkMetrics for an inactive interface."""
        network = NetworkMetrics(
            interface="wlan0",
            ip_address=None,  # No IP when disconnected
            bytes_sent=0,
            bytes_received=0,
            packets_sent=0,
            packets_received=0,
            speed_upload=0.0,  # No traffic
            speed_download=0.0,
        )
        assert network.interface == "wlan0"
        assert network.ip_address is None
        assert network.bytes_sent == 0
        assert network.speed_upload == 0.0

    def test_network_metrics_loopback_interface(self):
        """Test NetworkMetrics for loopback interface."""
        network = NetworkMetrics(
            interface="lo",
            ip_address="127.0.0.1",
            bytes_sent=1000,
            bytes_received=1000,  # Loopback sends = receives
            packets_sent=10,
            packets_received=10,
            speed_upload=0.0,
            speed_download=0.0,
        )
        assert network.interface == "lo"
        assert network.ip_address == "127.0.0.1"
        assert network.bytes_sent == network.bytes_received


class TestSystemMetrics:
    """Test cases for SystemMetrics dataclass."""

    def test_system_metrics_creation(self):
        """Test SystemMetrics creation with typical values."""
        system = SystemMetrics(
            hostname="My Machine",
            os_name="Linux",
            kernel_version="generic",
            uptime_seconds=86400,
            user="tim",
            boot_time=1703980800.0,
        )
        assert system.hostname == "My Machine"
        assert system.os_name == "Linux"
        assert system.kernel_version == "generic"
        assert system.uptime_seconds == 86400
        assert system.user == "tim"
        assert system.boot_time == 1703980800.0


class TestTelemetryCollector:
    """Test cases for TelemetryCollector class."""

    @pytest.fixture
    def collector(self):
        """Create a TelemetryCollector instance for testing."""
        return TelemetryCollector()

    @pytest.fixture
    def cpu_mocks(self, mocker):
        """Set up CPU-related mocks with realistic defaults."""
        # psutil mocks (global functions)
        mock_cpu_percent = mocker.patch("psutil.cpu_percent")
        mock_cpu_freq = mocker.patch("psutil.cpu_freq")
        mock_cpu_count = mocker.patch("psutil.cpu_count")

        # File reading mock
        mock_open = mocker.mock_open(read_data="model name\t: AMD Ryzen 7 7800X3D\n")
        mocker.patch("builtins.open", mock_open)

        # Set sensible defaults
        mock_cpu_freq.return_value = mocker.MagicMock(current=3400.0)
        mock_cpu_count.return_value = 16
        mock_cpu_percent.side_effect = [25.5, [20.0, 30.0, 25.0, 25.0]]

        return {
            "cpu_percent": mock_cpu_percent,
            "cpu_freq": mock_cpu_freq,
            "cpu_count": mock_cpu_count,
            "file_open": mock_open,
        }

    @pytest.mark.asyncio
    async def test_collect_memory_metrics(self, collector, mocker):
        """Test memory metrics collectio nwith mocked psutil."""

        # Create fake psutil responses
        mock_virtual_memory = mocker.patch("psutil.virtual_memory")
        mock_disk_usage = mocker.patch("psutil.disk_usage")

        # Set up what the fake functions return
        mock_virtual_memory.return_value = mocker.MagicMock(
            used=16000000000,  # 16GB used
            total=32000000000,  # 32GB total
            percent=50.0,  # 50% usage
        )

        mock_disk_usage.return_value = mocker.MagicMock(
            used=500000000000,  # 500GB used
            total=1000000000000,  # 1TB total
            percent=50.0,  # 50% usage
        )

        result = await collector.collect_memory_metrics()

        # Verify results
        assert isinstance(result, MemoryMetrics)
        assert result.ram_used == 16000000000
        assert result.ram_total == 32000000000
        assert result.ram_percent == 50.0
        assert result.disk_used == 500000000000
        assert result.disk_total == 1000000000000
        assert result.disk_percent == 50.0

    @pytest.mark.asyncio
    async def test_collect_cpu_metrics_complete(self, collector, cpu_mocks, mocker):
        """Test CPU metrics collection with multiple mocks."""

        # cpu_temperature stays here (instance-specific)
        mock_get_cpu_temp = mocker.patch.object(collector, "_get_cpu_temperature")
        mock_get_cpu_temp.return_value = 45.0

        # Everything else comes from fixture with good defaults
        result = await collector.collect_cpu_metrics()

        # Verify results
        assert isinstance(result, CPUMetrics)
        assert result.temperature == 45.0
        assert result.usage_percent == 25.5
        assert result.frequency == 3400.0
        assert len(result.core_usage) == 4

    @pytest.mark.asyncio
    async def test_collect_cpu_metrics_no_temperature(
        self, collector, cpu_mocks, mocker
    ):
        """Test CPU metrics when temperature can't be read."""

        # Set temperature to fail from the beginning
        mock_get_cpu_temp = mocker.patch.object(collector, "_get_cpu_temperature")
        mock_get_cpu_temp.return_value = None  # Temperature unavailable

        # Call the method once
        result = await collector.collect_cpu_metrics()

        # Verify it handles missing temperature gracefully
        assert result.temperature is None
        assert result.usage_percent == 25.5

    @pytest.mark.asyncio
    async def test_collect_gpu_metrics_success(self, collector, mocker):
        """Test GPU metrics collection with successful data."""

        # Set up the cache directly instead of mocking methods
        collector._static_cache["gpu_name"] = "AMD Radeon RX 7900 XTX"
        collector._static_cache["gpu_total_vram"] = 24560

        # Mock _get_amdgpu_metrics with correct key names
        mock_get_amdgpu_metrics = mocker.patch.object(collector, "_get_amdgpu_metrics")
        mock_get_amdgpu_metrics.return_value = {
            "temperature": 65.0,
            "usage": 80.0,  # Note: 'usage' not 'usage_percent'
            "vram_used": 8000,  # Note: 'vram_used' not 'memory_used'
            "fan_speed": 1500,
            "clock_speed": "2400",
        }

        # Call the method
        result = await collector.collect_gpu_metrics()

        # Verify the result
        assert result is not None
        assert result.name == "AMD Radeon RX 7900 XTX"
        assert result.temperature == 65.0
        assert result.usage_percent == 80.0  # Gets mapped from 'usage'
        assert result.memory_used == 8000  # Gets mapped from 'vram_used'
        assert result.memory_total == 24560  # From cache
        assert result.fan_speed == 1500
        assert result.clock_speed == "2400"

    @pytest.mark.asyncio
    async def test_collect_gpu_metrics_no_gpu(self, collector, mocker):
        """Test GPU metrics when no GPU is found."""

        # Mock file reading to fail (no GPU files)
        mock_open = mocker.mock_open()
        mock_open.side_effect = FileNotFoundError("No GPU found")
        mocker.patch("builtins.open", mock_open)

        result = await collector.collect_gpu_metrics()

        # Should return None when no GPU found
        assert result is None

    @pytest.mark.asyncio
    async def test_collect_network_metrics(self, collector, mocker):
        """Test network metrics collection."""

        # Mock psutil network functions
        mock_net_io_counters = mocker.patch("psutil.net_io_counters")

        # Mock the IP address lookup method
        mock_get_interface_ip = mocker.patch.object(collector, "_get_interface_ip")
        mock_get_interface_ip.return_value = "192.168.1.100"

        # Mock network interface data
        mock_stats = mocker.MagicMock()
        mock_stats.bytes_sent = 1000000
        mock_stats.bytes_recv = 2000000
        mock_stats.packets_sent = 500
        mock_stats.packets_recv = 800

        mock_net_io_counters.return_value = {
            "eth0": mock_stats,
            "lo": mock_stats,  # Will be filtered out
        }

        result = await collector.collect_network_metrics()

        # Verify results
        assert isinstance(result, list)
        assert len(result) == 1  # Only eth0, lo filtered out

        network = result[0]
        assert isinstance(network, NetworkMetrics)
        assert network.interface == "eth0"
        assert network.ip_address == "192.168.1.100"
        assert network.bytes_sent == 1000000
        assert network.bytes_received == 2000000

    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, collector, mocker):
        """Test system metrics collection."""

        # Mock os functions
        mock_uname = mocker.patch("os.uname")
        mock_uname.return_value = mocker.MagicMock(
            nodename="test-machine", release="6.8.0-63-generic"
        )

        mock_getlogin = mocker.patch("os.getlogin")
        mock_getlogin.return_value = "testuser"

        # Mock psutil functions
        mock_boot_time = mocker.patch("psutil.boot_time")
        mock_boot_time.return_value = 1703980800.0

        # Mock time.time for uptime calculation
        mock_time = mocker.patch("time.time")
        mock_time.return_value = 1703980800.0 + 86400  # 1 day later

        # Mock the OS name method
        mock_get_os_name = mocker.patch.object(collector, "_get_os_name")
        mock_get_os_name.return_value = "Ubuntu 22.04"

        result = await collector.collect_system_metrics()

        # Verify results
        assert isinstance(result, SystemMetrics)
        assert result.hostname == "test-machine"
        assert result.os_name == "Ubuntu 22.04"
        assert result.kernel_version == "6.8.0-63-generic"
        assert result.uptime_seconds == 86400
        assert result.user == "testuser"
        assert result.boot_time == 1703980800.0

    @pytest.mark.asyncio
    async def test_caching_system(self, collector, mocker):
        """Test that static data is cached properly."""

        # Mock the static data collection methods (correct names)
        mock_get_gpu_name = mocker.patch.object(collector, "_get_gpu_name_static")
        mock_get_gpu_name.return_value = "AMD Radeon RX 7900 XTX"

        mock_get_gpu_vram = mocker.patch.object(
            collector, "_get_gpu_total_vram"
        )  # Fixed name
        mock_get_gpu_vram.return_value = 24560

        # Call cache initialization
        await collector._ensure_cache_initialized()

        # Verify cache was populated
        assert collector._static_cache["gpu_name"] == "AMD Radeon RX 7900 XTX"
        assert collector._static_cache["gpu_total_vram"] == 24560

        # Call again - should use cache, not call methods again
        mock_get_gpu_name.reset_mock()
        mock_get_gpu_vram.reset_mock()
        await collector._ensure_cache_initialized()

        # Verify methods weren't called again (cache was used)
        mock_get_gpu_name.assert_not_called()
        mock_get_gpu_vram.assert_not_called()

    @pytest.mark.asyncio
    async def test_collect_all_metrics_integration(self, collector, mocker):
        """Test that collect_all_metrics works with all components."""

        # Mock all the subsystems
        mock_cpu_metrics = mocker.patch.object(collector, "collect_cpu_metrics")
        mock_gpu_metrics = mocker.patch.object(collector, "collect_gpu_metrics")
        mock_memory_metrics = mocker.patch.object(collector, "collect_memory_metrics")
        mock_network_metrics = mocker.patch.object(collector, "collect_network_metrics")
        mock_system_metrics = mocker.patch.object(collector, "collect_system_metrics")

        # Set up return values
        mock_cpu_metrics.return_value = CPUMetrics(
            "AMD Ryzen", 45.0, 25.5, [20.0], 3400.0
        )
        mock_gpu_metrics.return_value = GPUMetrics(
            "AMD GPU", 65.0, 80.0, 8000, 24000, 1500, "2100"
        )
        mock_memory_metrics.return_value = MemoryMetrics(
            16000000000, 32000000000, 50.0, 500000000000, 1000000000000, 50.0
        )
        mock_network_metrics.return_value = [
            NetworkMetrics(
                "eth0", "192.168.1.100", 1000000, 2000000, 500, 800, 1024.0, 2048.0
            )
        ]
        mock_system_metrics.return_value = SystemMetrics(
            "test-machine", "Ubuntu", "6.8.0", 86400, "user", 1703980800.0
        )

        result = await collector.collect_all_metrics()

        # Verify all methods were called
        mock_cpu_metrics.assert_called_once()
        mock_gpu_metrics.assert_called_once()
        mock_memory_metrics.assert_called_once()
        mock_network_metrics.assert_called_once()
        mock_system_metrics.assert_called_once()

        # Verify the result structure
        assert result.cpu.name == "AMD Ryzen"
        assert result.gpu.name == "AMD GPU"
        assert result.memory.ram_percent == 50.0
        assert len(result.network) == 1
        assert result.system.hostname == "test-machine"
        assert result.timestamp > 0

    @pytest.mark.asyncio
    async def test_debug_methods(self, collector):
        """Debug to see what methods exist."""
        methods = [method for method in dir(collector) if not method.startswith("__")]
        print("Available methods:")
        for method in sorted(methods):
            print(f"  {method}")
