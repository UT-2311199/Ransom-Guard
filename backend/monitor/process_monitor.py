import asyncio
import threading
from datetime import datetime
from typing import List, Optional, Dict
from collections import deque
import psutil

from utils.logger import setup_logger
from utils.helpers import generate_id

logger = setup_logger("process_monitor", "logs/monitor.log")

# In-memory process snapshot storage
process_snapshots: deque = deque(maxlen=100)
process_lock = threading.Lock()

# Suspicious process name patterns
SUSPICIOUS_PROCESS_NAMES = {
    "ransomware", "cryptolocker", "wannacry", "petya",
    "notpetya", "locky", "cerber", "ryuk", "sodinokibi",
    "maze", "netwalker", "revil", "darkside",
    "vssadmin",  # Volume Shadow Copy - commonly abused
    "wbadmin",   # Windows Backup - commonly abused
    "cipher",    # Windows encryption tool
    "bcdedit",   # Boot config - commonly modified by ransomware
}

# Suspicious executable paths
SUSPICIOUS_PATHS = {
    "/tmp/", "/var/tmp/", "\\temp\\", "\\tmp\\",
    "appdata\\local\\temp", "appdata\\roaming",
}


class ProcessMonitor:
    """
    Monitors running processes using psutil and detects suspicious behavior.
    """

    def __init__(self, scan_interval: int = 5):
        """
        Initialize the process monitor.

        Args:
            scan_interval: Seconds between process scans
        """
        self.scan_interval = scan_interval
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self._stop_event = asyncio.Event()

    async def start_monitoring(self):
        """
        Start the async process monitoring loop.
        """
        self.is_running = True
        self.start_time = datetime.utcnow()
        self._stop_event.clear()

        logger.info(f"Process monitor started. Scan interval: {self.scan_interval}s")

        while not self._stop_event.is_set():
            try:
                processes = await asyncio.get_event_loop().run_in_executor(
                    None, self._scan_processes
                )

                with process_lock:
                    process_snapshots.appendleft(
                        {
                            "snapshot_id": generate_id(),
                            "timestamp": datetime.utcnow().isoformat(),
                            "processes": processes,
                            "total_count": len(processes),
                        }
                    )

                await asyncio.sleep(self.scan_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in process monitoring loop: {e}")
                await asyncio.sleep(self.scan_interval)

        self.is_running = False
        logger.info("Process monitor stopped")

    def stop(self):
        """Stop the process monitor."""
        self._stop_event.set()
        self.is_running = False
        logger.info("Process monitor stop requested")

    def _scan_processes(self) -> List[Dict]:
        """
        Scan all running processes and collect detailed information.

        Returns:
            List of process information dictionaries
        """
        processes = []

        for proc in psutil.process_iter():
            try:
                process_info = self._get_process_info(proc)
                if process_info:
                    processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Error reading process {proc.pid}: {e}")
                continue

        # Sort by CPU usage descending
        processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        return processes

    def _get_process_info(self, proc: psutil.Process) -> Optional[Dict]:
        """
        Extract detailed information from a process.

        Args:
            proc: psutil Process object

        Returns:
            Process information dictionary or None
        """
        try:
            with proc.oneshot():
                pid = proc.pid
                name = proc.name()
                status = proc.status()

                # CPU and memory
                cpu_percent = proc.cpu_percent(interval=None)
                mem_info = proc.memory_info()
                mem_percent = proc.memory_percent()

                # Executable path
                try:
                    exe = proc.exe()
                except (psutil.AccessDenied, psutil.ZombieProcess, OSError):
                    exe = None

                # Command line
                try:
                    cmdline = proc.cmdline()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    cmdline = []

                # Parent process
                try:
                    parent = proc.parent()
                    parent_pid = parent.pid if parent else None
                    parent_name = parent.name() if parent else None
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    parent_pid = None
                    parent_name = None

                # Create time
                try:
                    create_time_ts = proc.create_time()
                    create_time = datetime.fromtimestamp(create_time_ts).isoformat()
                except (OSError, ValueError):
                    create_time = None

                # Username
                try:
                    username = proc.username()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    username = None

                # Thread count
                try:
                    num_threads = proc.num_threads()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    num_threads = 0

                # File descriptors
                try:
                    num_fds = proc.num_fds()
                except (psutil.AccessDenied, AttributeError):
                    num_fds = None

                # IO counters
                disk_read_bytes = 0
                disk_write_bytes = 0
                try:
                    io_counters = proc.io_counters()
                    disk_read_bytes = io_counters.read_bytes
                    disk_write_bytes = io_counters.write_bytes
                except (psutil.AccessDenied, AttributeError, psutil.ZombieProcess):
                    pass

                # Network connections
                try:
                    connections = len(proc.connections())
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    connections = 0

                # Suspicion analysis
                is_suspicious, suspicion_score, suspicion_reasons = self._analyze_suspicion(
                    name=name,
                    exe=exe,
                    cpu_percent=cpu_percent,
                    mem_percent=mem_percent,
                    disk_write_bytes=disk_write_bytes,
                    connections=connections,
                )

                return {
                    "pid": pid,
                    "name": name,
                    "status": status,
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(mem_percent, 2),
                    "memory_rss": mem_info.rss,
                    "memory_vms": mem_info.vms,
                    "exe": exe,
                    "cmdline": cmdline[:5] if cmdline else [],
                    "create_time": create_time,
                    "username": username,
                    "parent_pid": parent_pid,
                    "parent_name": parent_name,
                    "num_threads": num_threads,
                    "num_fds": num_fds,
                    "disk_read_bytes": disk_read_bytes,
                    "disk_write_bytes": disk_write_bytes,
                    "connections": connections,
                    "is_suspicious": is_suspicious,
                    "suspicion_score": suspicion_score,
                    "suspicion_reasons": suspicion_reasons,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        except Exception as e:
            logger.debug(f"Error getting process info: {e}")
            return None

    def _analyze_suspicion(
        self,
        name: str,
        exe: Optional[str],
        cpu_percent: float,
        mem_percent: float,
        disk_write_bytes: int,
        connections: int,
    ):
        """
        Analyze whether a process is suspicious.

        Returns:
            Tuple of (is_suspicious, suspicion_score, reasons)
        """
        score = 0.0
        reasons = []

        # Check suspicious process names
        name_lower = name.lower() if name else ""
        for suspicious_name in SUSPICIOUS_PROCESS_NAMES:
            if suspicious_name in name_lower:
                score += 40
                reasons.append(f"Suspicious process name: {name}")
                break

        # Check suspicious executable paths
        if exe:
            exe_lower = exe.lower()
            for suspicious_path in SUSPICIOUS_PATHS:
                if suspicious_path in exe_lower:
                    score += 25
                    reasons.append(f"Running from suspicious path: {exe}")
                    break

        # High CPU usage
        if cpu_percent > 80:
            score += 15
            reasons.append(f"High CPU usage: {cpu_percent:.1f}%")
        elif cpu_percent > 60:
            score += 8

        # High memory usage
        if mem_percent > 50:
            score += 10
            reasons.append(f"High memory usage: {mem_percent:.1f}%")
        elif mem_percent > 30:
            score += 5

        # Excessive disk writes (potential encryption activity)
        if disk_write_bytes > 100 * 1024 * 1024:  # 100MB
            score += 20
            reasons.append(f"Excessive disk writes: {disk_write_bytes / (1024*1024):.1f}MB")
        elif disk_write_bytes > 50 * 1024 * 1024:  # 50MB
            score += 10

        # Many network connections
        if connections > 100:
            score += 15
            reasons.append(f"Excessive network connections: {connections}")
        elif connections > 50:
            score += 7

        is_suspicious = score >= 30
        return is_suspicious, min(round(score, 2), 100.0), reasons

    def get_current_processes(self) -> List[Dict]:
        """Get the latest process snapshot."""
        with process_lock:
            if process_snapshots:
                return process_snapshots[0].get("processes", [])
        return self._scan_processes()

    def get_suspicious_processes(self) -> List[Dict]:
        """Get only suspicious processes from the latest snapshot."""
        processes = self.get_current_processes()
        return [p for p in processes if p.get("is_suspicious")]

    def terminate_process(self, pid: int, force: bool = False) -> Dict:
        """
        Terminate a process by PID.

        Args:
            pid: Process ID to terminate
            force: Use SIGKILL instead of SIGTERM

        Returns:
            Result dictionary
        """
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()

            if force:
                proc.kill()
                action = "killed"
            else:
                proc.terminate()
                action = "terminated"

            logger.warning(f"Process {proc_name} (PID: {pid}) {action}")

            return {
                "success": True,
                "pid": pid,
                "process_name": proc_name,
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except psutil.NoSuchProcess:
            return {
                "success": False,
                "pid": pid,
                "error": f"Process {pid} does not exist",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except psutil.AccessDenied:
            return {
                "success": False,
                "pid": pid,
                "error": f"Access denied to terminate process {pid}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "success": False,
                "pid": pid,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


def get_process_list() -> List[Dict]:
    """
    Standalone function to get current process list.

    Returns:
        List of process dictionaries
    """
    with process_lock:
        if process_snapshots:
            return process_snapshots[0].get("processes", [])

    # Fallback: direct scan
    monitor = ProcessMonitor()
    return monitor._scan_processes()