from datetime import datetime

from fastapi import APIRouter, HTTPException

from services.threat_service import get_threat_service
from utils.logger import setup_logger

logger = setup_logger("routes.analytics", "logs/app.log")

router = APIRouter()


@router.get("/analytics", summary="Get analytics data")
async def get_analytics():
    """
    Retrieve comprehensive analytics data for the dashboard.

    Includes:
    - Threat summary statistics
    - Threats by severity level
    - Daily threat trends
    - Top targeted file extensions
    - Top suspicious processes
    - Status distribution
    """
    try:
        service = get_threat_service()
        data = await service.get_analytics()

        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"GET /analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))