from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from services.system_service import get_system_service
from utils.logger import setup_logger

logger = setup_logger("routes.system", "logs/app.log")

router = APIRouter()


@router.get("/system", summary="Get complete system information")
async def get_system_info():
    """
    Retrieve complete system information including CPU, memory, disk, and network.
    """
    try:
        service = get_system_service()
        data = service.get_system_info()
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"GET /system error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cpu", summary="Get CPU information")
async def get_cpu_info():
    """
    Retrieve detailed CPU usage and core information.
    """
    try:
        service = get_system_service()
        data = service.get_cpu_info()
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"GET /cpu error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory", summary="Get memory information")
async def get_memory_info():
    """
    Retrieve RAM usage and availability information.
    """
    try:
        service = get_system_service()
        data = service.get_memory_info()
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"GET /memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disk", summary="Get disk information")
async def get_disk_info():
    """
    Retrieve disk usage for all partitions and I/O statistics.
    """
    try:
        service = get_system_service()
        data = service.get_disk_info()
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"GET /disk error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processes", summary="Get running processes")
async def get_processes(
    limit: int = 100,
    sort_by: str = "cpu_percent",
    suspicious_only: bool = False,
):
    """
    Retrieve list of running processes with detailed information.

    - **limit**: Maximum number of processes to return
    - **sort_by**: Sort field (cpu_percent, memory_percent, pid, name)
    - **suspicious_only**: Return only processes flagged as suspicious
    """
    try:
        from services.monitor_service import get_monitor_service
        service = get_monitor_service()

        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")

        valid_sort_fields = ["cpu_percent", "memory_percent", "pid", "name"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=400,
                detail=f"sort_by must be one of: {valid_sort_fields}",
            )

        data = service.get_processes(
            limit=limit,
            sort_by=sort_by,
            suspicious_only=suspicious_only,
        )
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /processes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))