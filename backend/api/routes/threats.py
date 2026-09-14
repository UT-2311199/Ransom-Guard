from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.threat_service import get_threat_service
from utils.logger import setup_logger

logger = setup_logger("routes.threats", "logs/threats.log")

router = APIRouter()


class ThreatStatusUpdate(BaseModel):
    threat_id: str
    status: str
    notes: Optional[str] = None


@router.get("/threats", summary="Get all threat logs")
async def get_threats(
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    status: Optional[str] = Query(
        None, description="Filter by status: active, resolved, quarantined, false_positive"
    ),
    threat_level: Optional[str] = Query(
        None, description="Filter by threat level: safe, low, medium, high, critical"
    ),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
):
    """
    Retrieve paginated threat logs with optional filtering.
    """
    try:
        # Validate status
        valid_statuses = ["active", "resolved", "quarantined", "false_positive", "investigating"]
        if status and status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"status must be one of: {valid_statuses}",
            )

        # Validate threat_level
        valid_levels = ["safe", "low", "medium", "high", "critical"]
        if threat_level and threat_level not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"threat_level must be one of: {valid_levels}",
            )

        service = get_threat_service()
        data = await service.get_threats(
            limit=limit,
            skip=skip,
            status=status,
            threat_level=threat_level,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /threats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threats/summary", summary="Get threat summary statistics")
async def get_threat_summary():
    """
    Retrieve summary statistics for all threats.
    """
    try:
        service = get_threat_service()
        data = await service.get_threat_summary()
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"GET /threats/summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/threats/status", summary="Update threat status")
async def update_threat_status(request: ThreatStatusUpdate):
    """
    Update the status of a threat record.

    - **threat_id**: Threat ID to update
    - **status**: New status (active, resolved, quarantined, false_positive, investigating)
    - **notes**: Optional notes about the status change
    """
    try:
        valid_statuses = ["active", "resolved", "quarantined", "false_positive", "investigating"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"status must be one of: {valid_statuses}",
            )

        service = get_threat_service()
        result = await service.update_threat_status(
            threat_id=request.threat_id,
            status=request.status,
            notes=request.notes,
        )

        return {
            "success": result.get("success"),
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PUT /threats/status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))