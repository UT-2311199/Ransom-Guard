from datetime import datetime

from fastapi import APIRouter, HTTPException, Body

from schemas.prediction import PredictionRequest, TerminateRequest, QuarantineRequest
from services.prediction_service import get_prediction_service
from utils.logger import setup_logger

logger = setup_logger("routes.prediction", "logs/prediction.log")

router = APIRouter()


@router.post("/predict", summary="Predict ransomware threat")
async def predict_threat(request: PredictionRequest):
    """
    Analyze a file using the ML model and return threat assessment.

    Provide file path and optional metadata for analysis.
    The system will extract features and run the ransomware detection model.
    """
    try:
        service = get_prediction_service()

        data = {
            "file_path": request.file_path,
            "file_name": request.file_name,
            "file_extension": request.file_extension,
            "file_size": request.file_size,
            "entropy": request.entropy,
            "process_name": request.process_name,
            "process_id": request.process_id,
            "event_type": request.event_type,
            "rapid_changes": request.rapid_changes,
            "extensions_modified": request.extensions_modified,
            "suspicious_keywords": request.suspicious_keywords,
        }

        result = await service.predict(data)

        return {
            "success": True,
            "result": result,
            "message": f"Prediction complete. Threat level: {result['threat_level'].upper()}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"POST /predict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/terminate", summary="Terminate a suspicious process")
async def terminate_process(request: TerminateRequest):
    """
    Terminate a process by PID.

    - **pid**: Process ID to terminate
    - **reason**: Reason for termination (logged)
    - **force**: Use SIGKILL instead of SIGTERM
    """
    try:
        # Safety check: prevent terminating critical system processes
        PROTECTED_PIDS = {0, 1}
        if request.pid in PROTECTED_PIDS:
            raise HTTPException(
                status_code=403,
                detail=f"PID {request.pid} is a protected system process and cannot be terminated",
            )

        service = get_prediction_service()
        result = await service.terminate_process(
            pid=request.pid,
            reason=request.reason,
            force=request.force,
        )

        status_code = 200 if result.get("success") else 400
        return {
            "success": result.get("success"),
            "result": result,
            "message": (
                f"Process {request.pid} terminated successfully"
                if result.get("success")
                else f"Failed to terminate process: {result.get('error')}"
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /terminate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quarantine", summary="Quarantine a suspicious file")
async def quarantine_file(request: QuarantineRequest):
    """
    Move a suspicious file to the quarantine directory.

    - **file_path**: Full path of the file to quarantine
    - **threat_id**: Optional associated threat log ID
    - **reason**: Reason for quarantine
    """
    try:
        service = get_prediction_service()
        result = await service.quarantine_file(
            file_path=request.file_path,
            threat_id=request.threat_id,
            reason=request.reason,
        )

        return {
            "success": result.get("success"),
            "result": result,
            "message": (
                f"File quarantined successfully: {request.file_path}"
                if result.get("success")
                else f"Quarantine failed: {result.get('error')}"
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /quarantine error: {e}")
        raise HTTPException(status_code=500, detail=str(e))