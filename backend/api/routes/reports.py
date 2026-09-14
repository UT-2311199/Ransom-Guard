import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from schemas.report import ReportRequest
from services.report_service import get_report_service
from utils.helpers import generate_id
from utils.logger import setup_logger

logger = setup_logger("routes.reports", "logs/reports.log")

router = APIRouter()


@router.get("/reports", summary="Get list of generated reports")
async def get_reports(
    limit: int = Query(50, ge=1, le=200, description="Maximum reports to return"),
    skip: int = Query(0, ge=0, description="Records to skip"),
):
    """
    Retrieve list of all generated reports.
    """
    try:
        service = get_report_service()
        data = await service.get_reports(limit=limit, skip=skip)

        # Add download URLs
        for report in data.get("reports", []):
            report["download_url"] = f"/api/v1/reports/{report['report_id']}/download"

        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"GET /reports error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports", summary="Generate a new report")
async def generate_report(request: ReportRequest):
    """
    Generate a new report in PDF, CSV, or JSON format.

    - **report_type**: Type of report (threat_summary, incident_report, system_status, full_audit)
    - **format**: Output format (pdf, csv, json)
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    - **include_system_info**: Include system information in report
    - **include_threats**: Include threat data in report
    - **title**: Optional report title
    """
    try:
        service = get_report_service()

        report_meta = await service.generate_report(
            report_type=request.report_type.value,
            format=request.format.value,
            start_date=request.start_date,
            end_date=request.end_date,
            include_system_info=request.include_system_info,
            include_threats=request.include_threats,
            title=request.title,
        )

        return {
            "success": True,
            "report": report_meta,
            "download_url": f"/api/v1/reports/{report_meta['report_id']}/download",
            "message": f"Report generated successfully: {report_meta['file_name']}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"POST /reports error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}/download", summary="Download a report")
async def download_report(report_id: str):
    """
    Download a generated report by its ID.
    """
    try:
        from database.connection import get_collection
        collection = get_collection("reports")

        # Find the report
        report = await collection.find_one({"report_id": report_id})

        if not report:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        file_path = report.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Report file not found on disk. It may have been deleted.",
            )

        # Determine media type
        format_types = {
            "pdf": "application/pdf",
            "csv": "text/csv",
            "json": "application/json",
        }
        report_format = report.get("format", "pdf")
        media_type = format_types.get(report_format, "application/octet-stream")

        return FileResponse(
            path=file_path,
            filename=report.get("file_name", os.path.basename(file_path)),
            media_type=media_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /reports/{report_id}/download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))