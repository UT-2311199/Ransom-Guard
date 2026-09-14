"""
backend/api/routes/ml_status.py

Endpoints exposing the ML module status and direct feature-based inference.
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ml_bridge import get_ml_status, predict_from_features, is_ml_available
from utils.logger import setup_logger

logger = setup_logger("routes.ml_status", "logs/prediction.log")

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────────────────────

class MLFeaturesRequest(BaseModel):
    """Direct behavioral feature vector for ML inference."""
    files_modified_per_sec: float = Field(0.0, ge=0, description="Files modified per second")
    files_created: float = Field(0.0, ge=0, description="Files created count")
    files_deleted: float = Field(0.0, ge=0, description="Files deleted count")
    rename_operations: float = Field(0.0, ge=0, description="Rename operations count")
    read_operations: float = Field(0.0, ge=0, description="Read operations count")
    write_operations: float = Field(0.0, ge=0, description="Write operations count")
    entropy: float = Field(0.0, ge=0.0, le=8.0, description="File entropy (0-8)")
    cpu_usage: float = Field(0.0, ge=0.0, le=100.0, description="CPU usage %")
    memory_usage: float = Field(0.0, ge=0.0, le=100.0, description="Memory usage %")
    disk_io: float = Field(0.0, ge=0, description="Disk I/O bytes")
    extension_changes: float = Field(0.0, ge=0, description="Extension change count")
    directories_accessed: float = Field(0.0, ge=0, description="Directories accessed count")
    encryption_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Encryption ratio (0-1)")


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/ml/status", summary="Get ML module status")
async def get_ml_module_status():
    """
    Returns the status of the trained ML model:
    - Whether it's loaded and ready
    - Model name, feature count, model path
    - Any initialization errors
    """
    try:
        status = get_ml_status()
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"GET /ml/status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/predict-features", summary="Direct ML inference from behavioral features")
async def predict_from_behavioral_features(request: MLFeaturesRequest):
    """
    Run the trained ML model directly on raw behavioral features.

    Unlike `POST /predict` (which accepts file paths), this endpoint
    accepts the exact behavioral feature vector the ML model expects:
    file activity rates, entropy, CPU/memory usage, encryption ratio, etc.

    Useful for:
    - Testing the ML model directly
    - Integration with live system monitors that collect behavioral metrics
    - Benchmarking predictions
    """
    if not is_ml_available():
        raise HTTPException(
            status_code=503,
            detail="ML model not available. Run `python ml/main.py --mode train` to train a model first.",
        )

    try:
        features: Dict[str, float] = request.model_dump()
        result = predict_from_features(features)

        if result is None:
            raise HTTPException(status_code=500, detail="ML prediction returned no result.")

        return {
            "success": True,
            "result": result,
            "message": f"Prediction: {result.get('label', 'UNKNOWN')} | Risk: {result.get('risk_level', 'UNKNOWN')} | Probability: {result.get('probability', 0):.2%}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /ml/predict-features error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
