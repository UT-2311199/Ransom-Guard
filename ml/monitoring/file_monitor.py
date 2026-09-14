# ml/monitoring/file_monitor.py

import os
import threading
import time
from typing import Callable, Optional

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from ml.feature_extractor.extractor import FeatureExtractor
from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, MonitoringConfig

logger = get_logger(__name__)


class RansomGuardFileHandler(FileSystemEventHandler):
    """
    Handles file system events and routes them to the FeatureExtractor.
    Ignores events from the quarantine directory, backup directory,
    and log directories to avoid feedback loops.
    """

    IGNORED_DIRS = {
        "quarantine",
        "backups",
        "logs",
        ".git",
        "__pycache__",
        ".pytest_cache",
    }

    def __init__(
        self,
        extractor: FeatureExtractor,
        alert_callback: Optional[Callable[[str, str], None]] = None,
    ):
        super().__init__()
        self.extractor = extractor
        self.alert_callback = alert_callback
        self._event_count = 0
        self._lock = threading.Lock()

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory and not self._is_ignored(event.src_path):
            self.extractor.on_file_created(event.src_path)
            self._increment_count()

    def on_deleted(self, event: FileDeletedEvent) -> None:
        if not event.is_directory and not self._is_ignored(event.src_path):
            self.extractor.on_file_deleted(event.src_path)
            self._increment_count()

    def on_modified(self, event: FileModifiedEvent) -> None:
        if not event.is_directory and not self._is_ignored(event.src_path):
            self.extractor.on_file_modified(event.src_path)
            self._increment_count()

    def on_moved(self, event: FileMovedEvent) -> None:
        if not event.is_directory and not self._is_ignored(event.src_path):
            self.extractor.on_file_moved(event.src_path, event.dest_path)
            self._increment_count()

    def get_event_count(self) -> int:
        """Return total events processed."""
        with self._lock:
            return self._event_count

    def _increment_count(self) -> None:
        with self._lock:
            self._event_count += 1

    def _is_ignored(self, path: str) -> bool:
        """Check whether a path belongs to an ignored directory."""
        path_parts = set(os.path.normpath(path).split(os.sep))
        return bool(path_parts.intersection(self.IGNORED_DIRS))


class FileSystemMonitor:
    """
    Watches a directory tree for file system events using watchdog.
    Routes events to the FeatureExtractor for feature construction.
    """

    def __init__(
        self,
        extractor: FeatureExtractor,
        monitoring_config: Optional[MonitoringConfig] = None,
        alert_callback: Optional[Callable[[str, str], None]] = None,
    ):
        self.extractor = extractor
        self.config = monitoring_config or CONFIG.monitoring
        self.alert_callback = alert_callback

        self.handler = RansomGuardFileHandler(
            extractor=extractor,
            alert_callback=alert_callback,
        )
        self.observer = Observer()
        self._running = False
        self._watch_path: Optional[str] = None

    def start(self, watch_path: Optional[str] = None) -> None:
        """
        Start monitoring the specified directory.

        Args:
            watch_path: Directory to watch (uses config default if None)
        """
        self._watch_path = watch_path or self.config.watch_directory
        if not os.path.exists(self._watch_path):
            logger.warning(
                f"Watch directory does not exist: {self._watch_path}. Creating it."
            )
            os.makedirs(self._watch_path, exist_ok=True)

        self.observer.schedule(
            self.handler,
            path=self._watch_path,
            recursive=True,
        )
        self.observer.start()
        self._running = True
        logger.info(f"File system monitoring started: {self._watch_path}")

    def stop(self) -> None:
        """Stop the file system observer."""
        if self._running:
            self.observer.stop()
            self.observer.join(timeout=5)
            self._running = False
            logger.info("File system monitoring stopped.")

    def is_running(self) -> bool:
        """Return whether monitoring is active."""
        return self._running and self.observer.is_alive()

    def get_watch_path(self) -> Optional[str]:
        """Return the monitored directory path."""
        return self._watch_path

    def get_event_count(self) -> int:
        """Return total file events processed."""
        return self.handler.get_event_count()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()