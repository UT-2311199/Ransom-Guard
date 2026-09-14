# ml/monitoring/process_monitor.py

import threading
import time
from typing import Any, Callable, Dict, List, Optional

import psutil

from ml.feature_extractor.extractor import FeatureExtractor
from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, MonitoringConfig

logger = get_logger(__name__)


# Suspicious process names (partial match) — augment as needed
SUSPICIOUS_PROCESS_NAMES = {
    "vssadmin",     # Shadow copy deletion
    "bcdedit",      # Boot config modification
    "wbadmin",      # Backup deletion
    "powershell",   # Script execution
    "cmd",          # Command execution
    "wscript",      # Script host
    "cscript",      # Script host
    "mshta",        # HTML application host
    "certutil",     # Certificate utility (sometimes abused)
    "regsvr32",     # COM registration (abuse vector)
    "rundll32",     # DLL execution
}


class ProcessMonitor:
    """
    Monitors running processes and system resources using psutil.
    Collects CPU, memory, disk I/O metrics and detects suspicious processes.
    Feeds data into the FeatureExtractor.
    """

    def __init__(
        self,
        extractor: FeatureExtractor,
        monitoring_config: Optional[MonitoringConfig] = None,
        alert_callback: Optional[Callable[[str, Dict], None]] = None,
    ):
        self.extractor = extractor
        self.config = monitoring_config or CONFIG.monitoring
        self.alert_callback = alert_callback

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        # Track previous disk I/O for delta computation
        self._prev_disk_io: Optional[psutil._common.sdiskio] = None
        self._prev_disk_time: float = time.time()

        self._suspicious_processes_found: List[str] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start process monitoring in a background thread."""
        if self._running:
            logger.warning("ProcessMonitor already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitor_loop,
            name="RansomGuard-ProcessMonitor",
            daemon=True,
        )
        self._thread.start()
        self._running = True
        logger.info(
            f"Process monitoring started (interval={self.config.process_poll_interval}s)"
        )

    def stop(self) -> None:
        """Stop the process monitor thread."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._running = False
        logger.info("Process monitoring stopped.")

    def is_running(self) -> bool:
        """Return whether monitor is active."""
        return self._running

    def get_suspicious_processes(self) -> List[str]:
        """Return list of detected suspicious process names."""
        with self._lock:
            return list(self._suspicious_processes_found)

    # ------------------------------------------------------------------
    # Snapshot Methods (Public)
    # ------------------------------------------------------------------

    def get_current_metrics(self) -> Dict[str, float]:
        """
        Take an immediate system metrics snapshot.

        Returns:
            Dictionary with cpu_percent, memory_percent, disk_io_bytes_per_sec
        """
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        disk_io = self._compute_disk_io_rate()

        return {
            "cpu_usage": cpu,
            "memory_usage": mem,
            "disk_io": disk_io,
        }

    def get_process_list(self) -> List[Dict[str, Any]]:
        """
        Return a snapshot of all running processes with key attributes.

        Returns:
            List of process info dictionaries
        """
        processes = []
        for proc in psutil.process_iter(
            attrs=["pid", "name", "cpu_percent", "memory_percent", "status", "create_time"]
        ):
            try:
                info = proc.info
                info["suspicious"] = self._is_suspicious(info.get("name", ""))
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes

    def kill_process(self, pid: int) -> bool:
        """
        Terminate a process by PID.

        Args:
            pid: Process ID to kill

        Returns:
            True if successful, False otherwise
        """
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc.kill()
            logger.critical(f"Process killed: {proc_name} (PID={pid})")
            return True
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} not found.")
            return False
        except psutil.AccessDenied:
            logger.error(f"Access denied killing process {pid}.")
            return False
        except Exception as exc:
            logger.error(f"Failed to kill process {pid}: {exc}")
            return False

    # ------------------------------------------------------------------
    # Private: Monitoring Loop
    # ------------------------------------------------------------------

    def _monitor_loop(self) -> None:
        """Main monitoring loop — runs in background thread."""
        logger.debug("ProcessMonitor loop started.")

        while not self._stop_event.is_set():
            try:
                metrics = self.get_current_metrics()

                # Feed metrics to feature extractor
                self.extractor.update_system_metrics(
                    cpu_percent=metrics["cpu_usage"],
                    memory_percent=metrics["memory_usage"],
                    disk_io_bytes=metrics["disk_io"],
                )

                # Scan for suspicious processes
                self._scan_suspicious_processes()

            except Exception as exc:
                logger.error(f"ProcessMonitor loop error: {exc}")

            self._stop_event.wait(timeout=self.config.process_poll_interval)

        logger.debug("ProcessMonitor loop exited.")

    def _scan_suspicious_processes(self) -> None:
        """Scan running processes for suspicious names."""
        found = []
        for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
            try:
                name = (proc.info.get("name") or "").lower()
                cmdline = " ".join(proc.info.get("cmdline") or []).lower()

                if self._is_suspicious(name):
                    found.append(name)
                    event_data = {
                        "pid": proc.pid,
                        "name": name,
                        "cmdline": cmdline,
                        "event_type": "suspicious_process",
                    }
                    self.extractor.on_process_event(event_data)

                    if self.alert_callback:
                        self.alert_callback("suspicious_process", event_data)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        with self._lock:
            self._suspicious_processes_found = list(set(found))

    def _compute_disk_io_rate(self) -> float:
        """
        Compute disk I/O rate (bytes/sec) since last call.

        Returns:
            Bytes per second read+written
        """
        try:
            current_io = psutil.disk_io_counters()
            if current_io is None:
                return 0.0

            now = time.time()

            if self._prev_disk_io is None:
                self._prev_disk_io = current_io
                self._prev_disk_time = now
                return 0.0

            elapsed = max(now - self._prev_disk_time, 0.001)
            read_delta = current_io.read_bytes - self._prev_disk_io.read_bytes
            write_delta = current_io.write_bytes - self._prev_disk_io.write_bytes
            rate = (read_delta + write_delta) / elapsed

            self._prev_disk_io = current_io
            self._prev_disk_time = now

            return max(float(rate), 0.0)

        except Exception as exc:
            logger.debug(f"Disk IO computation error: {exc}")
            return 0.0

    @staticmethod
    def _is_suspicious(process_name: str) -> bool:
        """Check if a process name matches known suspicious patterns."""
        name_lower = process_name.lower()
        return any(s in name_lower for s in SUSPICIOUS_PROCESS_NAMES)