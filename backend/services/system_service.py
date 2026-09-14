import platform
import socket
from datetime import datetime
from typing import Dict, Any

import psutil

from utils.logger import setup_logger
from utils.helpers import bytes_to_gb

logger = setup_logger("system_service", "logs/app.log")


class SystemService:
    """Service for collecting system information using psutil."""

    def get_cpu_info(self) -> Dict[str, Any]:
        """
        Collect detailed CPU information.

        Returns:
            CPU information dictionary
        """
        try:
            freq = psutil.cpu_freq()
            return {
                "percent": psutil.cpu_percent(interval=0.1),
                "count_logical": psutil.cpu_count(logical=True),
                "count_physical": psutil.cpu_count(logical=False),
                "frequency_current": round(freq.current, 2) if freq else None,
                "frequency_max": round(freq.max, 2) if freq else None,
                "per_core_percent": psutil.cpu_percent(interval=0.1, percpu=True),
            }
        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")
            return {
                "percent": 0.0,
                "count_logical": 0,
                "count_physical": 0,
                "frequency_current": None,
                "frequency_max": None,
                "per_core_percent": [],
            }

    def get_memory_info(self) -> Dict[str, Any]:
        """
        Collect memory information.

        Returns:
            Memory information dictionary
        """
        try:
            mem = psutil.virtual_memory()
            return {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "percent": mem.percent,
                "total_gb": bytes_to_gb(mem.total),
                "used_gb": bytes_to_gb(mem.used),
                "available_gb": bytes_to_gb(mem.available),
            }
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {
                "total": 0,
                "available": 0,
                "used": 0,
                "percent": 0.0,
                "total_gb": 0.0,
                "used_gb": 0.0,
                "available_gb": 0.0,
            }

    def get_disk_info(self) -> Dict[str, Any]:
        """
        Collect disk information for all partitions.

        Returns:
            Disk information dictionary
        """
        try:
            partitions = []
            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append(
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent,
                            "total_gb": bytes_to_gb(usage.total),
                            "used_gb": bytes_to_gb(usage.used),
                            "free_gb": bytes_to_gb(usage.free),
                        }
                    )
                except (PermissionError, OSError):
                    continue

            # Disk I/O counters
            io_counters = psutil.disk_io_counters()
            return {
                "partitions": partitions,
                "read_bytes": io_counters.read_bytes if io_counters else 0,
                "write_bytes": io_counters.write_bytes if io_counters else 0,
                "read_count": io_counters.read_count if io_counters else 0,
                "write_count": io_counters.write_count if io_counters else 0,
            }

        except Exception as e:
            logger.error(f"Error getting disk info: {e}")
            return {
                "partitions": [],
                "read_bytes": 0,
                "write_bytes": 0,
                "read_count": 0,
                "write_count": 0,
            }

    def get_network_info(self) -> Dict[str, Any]:
        """
        Collect network information.

        Returns:
            Network information dictionary
        """
        try:
            net_io = psutil.net_io_counters()
            connections = len(psutil.net_connections())
            return {
                "bytes_sent": net_io.bytes_sent if net_io else 0,
                "bytes_recv": net_io.bytes_recv if net_io else 0,
                "packets_sent": net_io.packets_sent if net_io else 0,
                "packets_recv": net_io.packets_recv if net_io else 0,
                "connections_count": connections,
            }
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0,
                "connections_count": 0,
            }

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get complete system information.

        Returns:
            Complete system information dictionary
        """
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = (datetime.now() - boot_time).total_seconds()

            return {
                "hostname": socket.gethostname(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "boot_time": boot_time.isoformat(),
                "uptime_seconds": uptime,
                "cpu": self.get_cpu_info(),
                "memory": self.get_memory_info(),
                "disk": self.get_disk_info(),
                "network": self.get_network_info(),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            raise


# Singleton
_system_service = None


def get_system_service() -> SystemService:
    global _system_service
    if _system_service is None:
        _system_service = SystemService()
    return _system_service