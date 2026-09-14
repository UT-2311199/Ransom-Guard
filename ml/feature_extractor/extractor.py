# ml/feature_extractor/extractor.py

import math
import os
import time
from collections import Counter, deque
from threading import Lock
from typing import Dict, List, Optional, Any

import numpy as np

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, MonitoringConfig

logger = get_logger(__name__)

# Common ransomware file extensions
RANSOMWARE_EXTENSIONS = {
    ".encrypted", ".enc", ".locked", ".crypto", ".crypt", ".crypz",
    ".wnry", ".wncry", ".locky", ".cerber", ".zepto", ".thor",
    ".aaa", ".xyz", ".zzz", ".micro", ".ttt", ".mp3", ".vvv",
    ".crypted", ".crinf", ".r5a", ".xrtn", ".xtbl", ".ccc",
    ".rbobut", ".supercrypt", ".enigma", ".darkness", ".kraken",
}

BENIGN_EXTENSIONS = {
    ".txt", ".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt",
    ".jpg", ".png", ".mp4", ".mp3", ".zip", ".py", ".js", ".html",
    ".css", ".json", ".xml", ".csv", ".log",
}


class FeatureExtractor:
    """
    Extracts behavioral features from file system and process events
    collected over a sliding time window.
    """

    def __init__(
        self,
        monitoring_config: Optional[MonitoringConfig] = None,
        window_seconds: float = 10.0,
    ):
        self.config = monitoring_config or CONFIG.monitoring
        self.window_seconds = window_seconds
        self._lock = Lock()

        # Event queues (timestamp, event_data)
        self._file_events: deque = deque()
        self._process_events: deque = deque()

        # Counters reset per window
        self._files_created: int = 0
        self._files_deleted: int = 0
        self._files_modified: int = 0
        self._rename_ops: int = 0
        self._read_ops: int = 0
        self._write_ops: int = 0
        self._extension_changes: int = 0
        self._directories_accessed: set = set()

        # Entropy tracking
        self._entropy_samples: List[float] = []

        # System resource snapshots
        self._cpu_samples: List[float] = []
        self._memory_samples: List[float] = []
        self._disk_io_samples: List[float] = []

        self._window_start: float = time.time()

    # ------------------------------------------------------------------
    # Event Ingestion
    # ------------------------------------------------------------------

    def on_file_created(self, path: str) -> None:
        """Record a file creation event."""
        with self._lock:
            now = time.time()
            self._files_created += 1
            self._file_events.append(("created", now, path))
            self._directories_accessed.add(os.path.dirname(path))
            self._maybe_sample_entropy(path)
            self._check_extension(path, created=True)

    def on_file_deleted(self, path: str) -> None:
        """Record a file deletion event."""
        with self._lock:
            now = time.time()
            self._files_deleted += 1
            self._file_events.append(("deleted", now, path))
            self._directories_accessed.add(os.path.dirname(path))

    def on_file_modified(self, path: str) -> None:
        """Record a file modification event."""
        with self._lock:
            now = time.time()
            self._files_modified += 1
            self._write_ops += 1
            self._file_events.append(("modified", now, path))
            self._directories_accessed.add(os.path.dirname(path))
            self._maybe_sample_entropy(path)

    def on_file_moved(self, src_path: str, dest_path: str) -> None:
        """Record a file rename/move event."""
        with self._lock:
            now = time.time()
            self._rename_ops += 1
            self._file_events.append(("moved", now, src_path, dest_path))
            self._directories_accessed.add(os.path.dirname(dest_path))

            # Detect extension change
            src_ext = os.path.splitext(src_path)[1].lower()
            dst_ext = os.path.splitext(dest_path)[1].lower()
            if src_ext != dst_ext:
                self._extension_changes += 1
                if dst_ext in RANSOMWARE_EXTENSIONS:
                    logger.warning(
                        f"Ransomware extension detected: {src_path} -> {dest_path}"
                    )

    def on_process_event(self, event_data: Dict[str, Any]) -> None:
        """Record a process-level event."""
        with self._lock:
            now = time.time()
            self._process_events.append((now, event_data))

    def update_system_metrics(
        self,
        cpu_percent: float,
        memory_percent: float,
        disk_io_bytes: float,
    ) -> None:
        """Ingest current system resource metrics."""
        with self._lock:
            self._cpu_samples.append(cpu_percent)
            self._memory_samples.append(memory_percent)
            self._disk_io_samples.append(disk_io_bytes)

    # ------------------------------------------------------------------
    # Feature Vector Construction
    # ------------------------------------------------------------------

    def extract_features(self) -> Dict[str, float]:
        """
        Build and return the current feature vector.

        Returns:
            Dictionary of feature_name -> value
        """
        with self._lock:
            now = time.time()
            elapsed = max(now - self._window_start, 1.0)  # at least 1 second

            files_modified_per_sec = self._files_modified / elapsed

            # Remove stale events outside window
            self._prune_old_events(now)

            entropy = self._compute_mean_entropy()
            cpu = float(np.mean(self._cpu_samples)) if self._cpu_samples else 0.0
            memory = float(np.mean(self._memory_samples)) if self._memory_samples else 0.0
            disk_io = float(np.mean(self._disk_io_samples)) if self._disk_io_samples else 0.0
            encryption_ratio = self._compute_encryption_ratio()

            features = {
                "files_modified_per_sec": round(files_modified_per_sec, 4),
                "files_created": float(self._files_created),
                "files_deleted": float(self._files_deleted),
                "rename_operations": float(self._rename_ops),
                "read_operations": float(self._read_ops),
                "write_operations": float(self._write_ops),
                "entropy": round(entropy, 4),
                "cpu_usage": round(cpu, 2),
                "memory_usage": round(memory, 2),
                "disk_io": round(disk_io, 2),
                "extension_changes": float(self._extension_changes),
                "directories_accessed": float(len(self._directories_accessed)),
                "encryption_ratio": round(encryption_ratio, 4),
            }

            return features

    def reset_window(self) -> None:
        """Reset all counters for the next time window."""
        with self._lock:
            self._files_created = 0
            self._files_deleted = 0
            self._files_modified = 0
            self._rename_ops = 0
            self._read_ops = 0
            self._write_ops = 0
            self._extension_changes = 0
            self._directories_accessed.clear()
            self._entropy_samples.clear()
            self._cpu_samples.clear()
            self._memory_samples.clear()
            self._disk_io_samples.clear()
            self._file_events.clear()
            self._process_events.clear()
            self._window_start = time.time()
            logger.debug("FeatureExtractor window reset.")

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _prune_old_events(self, now: float) -> None:
        """Remove events older than the window from deques."""
        cutoff = now - self.window_seconds
        while self._file_events and self._file_events[0][1] < cutoff:
            self._file_events.popleft()
        while self._process_events and self._process_events[0][0] < cutoff:
            self._process_events.popleft()

    def _maybe_sample_entropy(self, path: str, max_read_bytes: int = 65536) -> None:
        """
        Attempt to compute byte entropy of a file.
        Silently fails if file is unreadable.
        """
        try:
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                with open(path, "rb") as f:
                    data = f.read(max_read_bytes)
                entropy = self._byte_entropy(data)
                self._entropy_samples.append(entropy)
        except (OSError, PermissionError):
            pass

    @staticmethod
    def _byte_entropy(data: bytes) -> float:
        """
        Compute Shannon entropy of a byte sequence.

        Returns:
            Entropy in bits (0.0 - 8.0)
        """
        if not data:
            return 0.0
        freq = Counter(data)
        n = len(data)
        entropy = 0.0
        for count in freq.values():
            p = count / n
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy

    def _compute_mean_entropy(self) -> float:
        """Return mean entropy from sampled files."""
        if not self._entropy_samples:
            return 0.0
        return float(np.mean(self._entropy_samples))

    def _compute_encryption_ratio(self) -> float:
        """
        Estimate the proportion of file operations involving
        ransomware-related extensions.
        """
        total_events = len(self._file_events)
        if total_events == 0:
            return 0.0

        ransom_events = 0
        for event in self._file_events:
            path = event[2] if len(event) > 2 else ""
            ext = os.path.splitext(path)[1].lower()
            if ext in RANSOMWARE_EXTENSIONS:
                ransom_events += 1

        # Also factor in extension changes
        change_contribution = min(self._extension_changes / max(total_events, 1), 1.0)
        base_ratio = ransom_events / total_events
        return min((base_ratio + change_contribution) / 2.0 + change_contribution * 0.3, 1.0)

    def _check_extension(self, path: str, created: bool = False) -> None:
        """Check if a newly created file has a suspicious extension."""
        ext = os.path.splitext(path)[1].lower()
        if ext in RANSOMWARE_EXTENSIONS:
            logger.warning(f"Suspicious extension on {'created' if created else 'modified'} file: {path}")