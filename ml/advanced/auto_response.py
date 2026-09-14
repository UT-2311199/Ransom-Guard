# ml/advanced/auto_response.py

import hashlib
import os
import shutil
import time
from typing import Any, Callable, Dict, List, Optional

import psutil

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, MonitoringConfig

logger = get_logger(__name__)


class AutoResponse:
    """
    Automated response system for detected ransomware activity.
    Supports:
    - Process auto-kill
    - File quarantine
    - Directory backup
    - Alert notification
    """

    def __init__(
        self,
        monitoring_config: Optional[MonitoringConfig] = None,
        notification_callback: Optional[Callable[[str, Dict], None]] = None,
    ):
        self.config = monitoring_config or CONFIG.monitoring
        self.notification_callback = notification_callback

        os.makedirs(self.config.quarantine_dir, exist_ok=True)
        os.makedirs(self.config.backup_dir, exist_ok=True)

        self._killed_pids: List[int] = []
        self._quarantined_files: List[str] = []
        self._backup_paths: List[str] = []

    # ------------------------------------------------------------------
    # Auto-Kill
    # ------------------------------------------------------------------

    def auto_kill_suspicious_processes(
        self,
        suspicious_names: Optional[List[str]] = None,
        high_cpu_threshold: float = 90.0,
        high_io_threshold: float = 100 * 1024 * 1024,  # 100 MB/s
    ) -> List[int]:
        """
        Kill processes that match suspicious criteria.

        Args:
            suspicious_names: List of process name substrings to kill
            high_cpu_threshold: CPU usage % above which to consider killing
            high_io_threshold: I/O bytes/sec above which to consider killing

        Returns:
            List of killed PIDs
        """
        if not self.config.auto_kill_enabled:
            logger.info("Auto-kill is disabled in config.")
            return []

        killed = []
        suspicious_names = suspicious_names or []

        for proc in psutil.process_iter(
            attrs=["pid", "name", "cpu_percent", "io_counters", "status"]
        ):
            try:
                if proc.info["status"] in (
                    psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD
                ):
                    continue

                name = (proc.info.get("name") or "").lower()
                pid = proc.info["pid"]

                # Skip system critical processes
                if self._is_system_critical(pid, name):
                    continue

                should_kill = False
                kill_reason = ""

                # Check name matching
                if any(sn.lower() in name for sn in suspicious_names):
                    should_kill = True
                    kill_reason = f"suspicious name: {name}"

                if should_kill:
                    if self._kill_process(pid, name, reason=kill_reason):
                        killed.append(pid)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return killed

    def kill_by_pid(self, pid: int, reason: str = "Manual kill") -> bool:
        """
        Kill a specific process by PID.

        Args:
            pid: Process ID
            reason: Reason for killing (for logging)

        Returns:
            True if successful
        """
        if not self.config.auto_kill_enabled:
            logger.warning("Auto-kill disabled. Enable in config to use this feature.")
            return False

        try:
            proc = psutil.Process(pid)
            return self._kill_process(pid, proc.name(), reason=reason)
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} not found.")
            return False

    # ------------------------------------------------------------------
    # Quarantine
    # ------------------------------------------------------------------

    def quarantine_file(self, file_path: str) -> Optional[str]:
        """
        Move a suspicious file to the quarantine directory.
        Renames it with a hash-based name to prevent accidental execution.

        Args:
            file_path: Path of the file to quarantine

        Returns:
            Quarantine path if successful, None otherwise
        """
        if not self.config.quarantine_enabled:
            logger.info("Quarantine is disabled in config.")
            return None

        if not os.path.exists(file_path):
            logger.warning(f"File to quarantine not found: {file_path}")
            return None

        try:
            file_hash = self._compute_file_hash(file_path)
            timestamp = int(time.time())
            quarantine_name = f"{timestamp}_{file_hash[:16]}.quarantine"
            quarantine_path = os.path.join(self.config.quarantine_dir, quarantine_name)

            # Create quarantine metadata
            meta_path = quarantine_path + ".meta"
            with open(meta_path, "w") as f:
                f.write(f"original_path={file_path}\n")
                f.write(f"quarantine_time={time.strftime('%Y-%m-%d %Human:%M:%S')}\n")
                f.write(f"sha256={file_hash}\n")

            shutil.move(file_path, quarantine_path)
            self._quarantined_files.append(quarantine_path)

            logger.warning(
                f"File quarantined: {file_path} -> {quarantine_path}"
            )

            if self.notification_callback:
                self.notification_callback(
                    "quarantine",
                    {"original": file_path, "quarantine": quarantine_path},
                )

            return quarantine_path

        except Exception as exc:
            logger.error(f"Quarantine failed for {file_path}: {exc}")
            return None

    def quarantine_directory(self, dir_path: str) -> List[str]:
        """
        Quarantine all files in a directory.

        Args:
            dir_path: Directory to quarantine

        Returns:
            List of quarantine paths
        """
        quarantined = []
        if not os.path.isdir(dir_path):
            return quarantined

        for root, _, files in os.walk(dir_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                result = self.quarantine_file(file_path)
                if result:
                    quarantined.append(result)

        return quarantined

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def backup_directory(
        self,
        source_dir: str,
        backup_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a timestamped backup of a directory.

        Args:
            source_dir: Directory to back up
            backup_name: Optional custom backup folder name

        Returns:
            Backup destination path if successful
        """
        if not os.path.isdir(source_dir):
            logger.error(f"Source directory not found: {source_dir}")
            return None

        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            name = backup_name or f"backup_{os.path.basename(source_dir)}_{timestamp}"
            dest = os.path.join(self.config.backup_dir, name)

            shutil.copytree(source_dir, dest)
            self._backup_paths.append(dest)

            logger.info(f"Backup created: {source_dir} -> {dest}")

            if self.notification_callback:
                self.notification_callback(
                    "backup", {"source": source_dir, "destination": dest}
                )

            return dest

        except Exception as exc:
            logger.error(f"Backup failed for {source_dir}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_response_summary(self) -> Dict[str, Any]:
        """Return summary of all response actions taken."""
        return {
            "killed_pids": list(self._killed_pids),
            "kill_count": len(self._killed_pids),
            "quarantined_files": list(self._quarantined_files),
            "quarantine_count": len(self._quarantined_files),
            "backup_paths": list(self._backup_paths),
            "backup_count": len(self._backup_paths),
        }

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _kill_process(self, pid: int, name: str, reason: str = "") -> bool:
        """Internal process kill with logging."""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()

            self._killed_pids.append(pid)
            logger.critical(f"Process killed: {name} (PID={pid}) | Reason: {reason}")

            if self.notification_callback:
                self.notification_callback(
                    "process_killed",
                    {"pid": pid, "name": name, "reason": reason},
                )
            return True

        except psutil.NoSuchProcess:
            logger.debug(f"Process {pid} already gone.")
            return False
        except psutil.AccessDenied:
            logger.error(f"Access denied killing {name} (PID={pid}).")
            return False

    @staticmethod
    def _is_system_critical(pid: int, name: str) -> bool:
        """Prevent killing critical system processes."""
        CRITICAL_PIDS = {0, 1, 2, 4}  # init, kernel, etc.
        CRITICAL_NAMES = {
            "systemd", "init", "kernel", "svchost", "csrss",
            "wininit", "lsass", "services", "winlogon",
        }
        if pid in CRITICAL_PIDS:
            return True
        return any(cn in name.lower() for cn in CRITICAL_NAMES)

    @staticmethod
    def _compute_file_hash(file_path: str, chunk_size: int = 65536) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    sha256.update(chunk)
        except (OSError, PermissionError):
            pass
        return sha256.hexdigest()