from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.monitor_service import get_monitor_service
from utils.logger import setup_logger

logger = setup_logger("routes.monitor", "logs/app.log")

router = APIRouter()


@router.get("/monitor/files", summary="Get file system events")
async def get_file_events(
    limit: int = Query(100, ge=1, le=5000, description="Maximum events to return"),
    event_type: Optional[str] = Query(
        None,
        description="Filter by event type: created, deleted, modified, renamed, moved, closed",
    ),
    page: int = Query(1, ge=1, description="Page number"),
):
    """
    Retrieve recent file system events captured by the watchdog monitor.

    - **limit**: Number of events per page
    - **event_type**: Filter by specific event type
    - **page**: Page number for pagination
    """
    try:
        # Validate event_type
        valid_types = ["created", "deleted", "modified", "renamed", "moved", "closed", "opened"]
        if event_type and event_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"event_type must be one of: {valid_types}",
            )

        service = get_monitor_service()
        data = await service.get_file_events(
            limit=limit,
            event_type=event_type,
            page=page,
        )

        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /monitor/files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/status", summary="Get monitor status")
async def get_monitor_status(request: object = None):
    """
    Get the current status of the file system monitor.
    """
    try:
        from fastapi import Request
        # Access app state for file monitor
        return {
            "success": True,
            "data": {
                "message": "Monitor status endpoint - check /monitor/files for events",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"GET /monitor/status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))