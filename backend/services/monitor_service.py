from datetime import datetime
from typing import List, Dict, Any, Optional

from database.connection import get_collection
from monitor.file_monitor import get_file_events
from monitor.process_monitor import get_process_list
from utils.logger import setup_logger
from utils.helpers import generate_id

logger = setup_logger("monitor_service", "logs/app.log")


class MonitorService:
    """Service for managing monitoring data and operations."""

    async def get_file_events(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Get file system events from the monitor.

        Args:
            limit: Maximum events to return
            event_type: Optional event type filter
            page: Page number for pagination

        Returns:
            Events data dictionary
        """
        try:
            events = get_file_events(limit=limit * page, event_type=event_type)

            # Pagination
            start = (page - 1) * limit
            end = start + limit
            paginated_events = events[start:end]

            # Log to database
            if paginated_events:
                await self._log_events_to_db(paginated_events[:10])

            return {
                "total": len(events),
                "page": page,
                "limit": limit,
                "events": paginated_events,
            }

        except Exception as e:
            logger.error(f"Error getting file events: {e}")
            raise

    async def _log_events_to_db(self, events: List[Dict]):
        """Log events to MongoDB system_logs collection."""
        try:
            collection = get_collection("system_logs")
            for event in events:
                event_doc = {
                    **event,
                    "log_id": generate_id(),
                    "log_type": "file_event",
                    "logged_at": datetime.utcnow(),
                }
                await collection.insert_one(event_doc)
        except Exception as e:
            logger.error(f"Error logging events to DB: {e}")

    def get_processes(
        self,
        limit: int = 100,
        sort_by: str = "cpu_percent",
        suspicious_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Get current process list.

        Args:
            limit: Maximum processes to return
            sort_by: Sort field
            suspicious_only: Return only suspicious processes

        Returns:
            Process data dictionary
        """
        try:
            processes = get_process_list()

            if suspicious_only:
                processes = [p for p in processes if p.get("is_suspicious")]

            # Sort
            valid_sort_fields = ["cpu_percent", "memory_percent", "pid", "name"]
            if sort_by in valid_sort_fields:
                processes = sorted(
                    processes,
                    key=lambda x: x.get(sort_by, 0),
                    reverse=sort_by in ["cpu_percent", "memory_percent"],
                )

            return {
                "total": len(processes),
                "processes": processes[:limit],
                "suspicious_count": sum(1 for p in processes if p.get("is_suspicious")),
            }

        except Exception as e:
            logger.error(f"Error getting processes: {e}")
            raise


def get_monitor_service() -> MonitorService:
    return MonitorService()