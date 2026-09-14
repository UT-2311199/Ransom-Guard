import os
import asyncio
import threading
from datetime import datetime
from typing import List, Optional, Callable
from collections import deque

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileClosedEvent,
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
)

from utils.logger import setup_logger
from utils.helpers import (
    get_file_extension,
    get_file_name,
    get_file_size,
    calculate_file_entropy,
    is_suspicious_extension,
    generate_id,
)

logger = setup_logger("file_monitor", "logs/monitor.log")

# In-memory event queue (max 5000 events)
event_queue: deque = deque(maxlen=5000)
event_lock = threading.Lock()


class RansomGuardEventHandler(FileSystemEventHandler):
    """
    Custom watchdog event handler that captures all file system events
    and stores them for analysis.
    """

    # Paths to ignore to reduce noise
    IGNORED_PATHS = {
        "/proc", "/sys", "/dev", "/run",
        "/tmp/.X", "/tmp/snap",
        "logs/", ".log", "__pycache__",
        ".pyc", ".git/",
    }

    def __init__(self):
        super().__init__()
        self.events_captured = 0
        self.start_time = datetime.utcnow()

    def _should_ignore(self, path: str) -> bool:
        """Check if the path should be ignored."""
        if not path:
            return True
        path_lower = path.lower()
        for ignored in self.IGNORED_PATHS:
            if ignored in path_lower:
                return True
        return False

    def _create_event_record(
        self,
        event_type: str,
        src_path: str,
        dest_path: Optional[str] = None,
        is_directory: bool = False,
    ) -> dict:
        """
        Create a standardized event record.

        Args:
            event_type: Type of file system event
            src_path: Source file path
            dest_path: Destination path (for move/rename events)
            is_directory: Whether the event is for a directory

        Returns:
            Event record dictionary
        """
        file_name = get_file_name(src_path)
        file_extension = get_file_extension(src_path)
        file_size = get_file_size(src_path) if event_type not in ["deleted"] else 0

        # Calculate entropy for non-directory, non-deleted files
        entropy = 0.0
        if not is_directory and event_type not in ["deleted", "created"]:
            entropy = calculate_file_entropy(src_path)

        suspicious_ext = is_suspicious_extension(file_extension) if file_extension else False

        record = {
            "event_id": generate_id(),
            "event_type": event_type,
            "file_path": src_path,
            "file_name": file_name,
            "file_extension": file_extension,
            "file_size": file_size,
            "is_directory": is_directory,
            "src_path": src_path,
            "dest_path": dest_path,
            "entropy": entropy,
            "is_suspicious_extension": suspicious_ext,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return record

    def _store_event(self, record: dict):
        """Store event in the in-memory queue."""
        with event_lock:
            event_queue.appendleft(record)
            self.events_captured += 1

        if self.events_captured % 100 == 0:
            logger.info(f"File monitor captured {self.events_captured} events total")

    def on_created(self, event):
        if self._should_ignore(event.src_path):
            return
        try:
            record = self._create_event_record(
                "created", event.src_path, is_directory=event.is_directory
            )
            self._store_event(record)
            logger.debug(f"Created: {event.src_path}")
        except Exception as e:
            logger.error(f"Error handling created event: {e}")

    def on_deleted(self, event):
        if self._should_ignore(event.src_path):
            return
        try:
            record = self._create_event_record(
                "deleted", event.src_path, is_directory=event.is_directory
            )
            self._store_event(record)
            logger.debug(f"Deleted: {event.src_path}")
        except Exception as e:
            logger.error(f"Error handling deleted event: {e}")

    def on_modified(self, event):
        if self._should_ignore(event.src_path):
            return
        try:
            record = self._create_event_record(
                "modified", event.src_path, is_directory=event.is_directory
            )
            self._store_event(record)
            logger.debug(f"Modified: {event.src_path}")
        except Exception as e:
            logger.error(f"Error handling modified event: {e}")

    def on_moved(self, event):
        if self._should_ignore(event.src_path):
            return
        try:
            record = self._create_event_record(
                "renamed",
                event.src_path,
                dest_path=event.dest_path,
                is_directory=event.is_directory,
            )
            self._store_event(record)
            logger.debug(f"Moved: {event.src_path} -> {event.dest_path}")
        except Exception as e:
            logger.error(f"Error handling moved event: {e}")

    def on_closed(self, event):
        if self._should_ignore(event.src_path):
            return
        try:
            record = self._create_event_record(
                "closed", event.src_path, is_directory=event.is_directory
            )
            self._store_event(record)
            logger.debug(f"Closed: {event.src_path}")
        except Exception as e:
            logger.error(f"Error handling closed event: {e}")


class FileSystemMonitor:
    """
    Manages the watchdog observer for real-time file system monitoring.
    """

    def __init__(self, watch_path: str = "/home"):
        self.watch_path = watch_path
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[RansomGuardEventHandler] = None
        self.is_running = False
        self.start_time: Optional[datetime] = None

    def start(self):
        """Start the file system monitor."""
        try:
            # Use home directory on Linux/Mac, C:\ on Windows
            if not os.path.exists(self.watch_path):
                self.watch_path = os.path.expanduser("~")

            self.event_handler = RansomGuardEventHandler()
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler,
                path=self.watch_path,
                recursive=True,
            )
            self.observer.start()
            self.is_running = True
            self.start_time = datetime.utcnow()

            logger.info(f"File system monitor started watching: {self.watch_path}")

        except Exception as e:
            logger.error(f"Failed to start file system monitor: {e}")
            self.is_running = False
            raise

    def stop(self):
        """Stop the file system monitor."""
        try:
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=5)
            self.is_running = False
            logger.info("File system monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping file system monitor: {e}")

    def get_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[dict]:
        """
        Get recent file system events.

        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type

        Returns:
            List of event records
        """
        with event_lock:
            events = list(event_queue)

        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]

        return events[:limit]

    def get_status(self) -> dict:
        """Get monitor status."""
        uptime = 0.0
        if self.start_time and self.is_running:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()

        events_captured = 0
        if self.event_handler:
            events_captured = self.event_handler.events_captured

        return {
            "is_active": self.is_running,
            "watch_path": self.watch_path,
            "events_captured": events_captured,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": uptime,
        }

    def clear_events(self):
        """Clear the event queue."""
        with event_lock:
            event_queue.clear()
        logger.info("Event queue cleared")


def get_file_events(limit: int = 100, event_type: Optional[str] = None) -> List[dict]:
    """
    Global function to access file events from the queue.

    Args:
        limit: Maximum events to return
        event_type: Optional filter

    Returns:
        List of events
    """
    with event_lock:
        events = list(event_queue)

    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]

    return events[:limit]