"""
backend/services/ml_bridge.py

Bridge between the FastAPI backend and the ML module (ml/).
Provides a singleton RansomwarePredictor that the backend
uses as its primary detection engine, with automatic fallback
to rule-based detection if the ML module is unavailable.
"""

import sys
import os
import psutil
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path so `ml.*` imports resolve
_PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.logger import setup_logger

logger = setup_logger("ml_bridge", "logs/prediction.log")

# ─── Singleton ───────────────────────────────────────────────────────────────

_predictor_instance = None
_predictor_loaded: bool = False
_predictor_error: Optional[str] = None


def get_ml_predictor():
    """
    Return the singleton RansomwarePredictor, loading it on first call.
    Returns None if the ML module or trained model is unavailable.
    """
    global _predictor_instance, _predictor_loaded, _predictor_error

    if _predictor_loaded:
        return _predictor_instance

    try:
        from ml.predictor.predictor import RansomwarePredictor
        predictor = RansomwarePredictor()
        predictor.load()
        _predictor_instance = predictor
        _predictor_loaded = True
        logger.info(
            f"ML bridge initialized — model: {predictor.model_name}, "
            f"features: {len(predictor.feature_names or [])}"
        )
    except FileNotFoundError:
        _predictor_error = "No trained model found. Run `python ml/main.py --mode train` first."
        logger.warning(f"ML bridge: {_predictor_error}")
        _predictor_loaded = True  # mark as attempted so we don't retry every request
    except ImportError as e:
        _predictor_error = f"ML module import error: {e}"
        logger.error(f"ML bridge: {_predictor_error}")
        _predictor_loaded = True
    except Exception as e:
        _predictor_error = f"ML bridge init error: {e}"
        logger.error(f"ML bridge: {_predictor_error}", exc_info=True)
        _predictor_loaded = True

    return _predictor_instance


def is_ml_available() -> bool:
    """Return True if ML predictor is loaded and ready."""
    return get_ml_predictor() is not None


def get_ml_status() -> Dict[str, Any]:
    """Return status dict about the ML module state."""
    predictor = get_ml_predictor()
    if predictor is None:
        return {
            "available": False,
            "error": _predictor_error,
            "model_name": None,
            "feature_count": 0,
            "model_path": None,
        }
    return {
        "available": True,
        "error": None,
        "model_name": predictor.model_name,
        "feature_count": len(predictor.feature_names or []),
        "feature_names": predictor.feature_names or [],
        "model_path": str(
            Path(_PROJECT_ROOT) / "ml" / "models" / "saved" / "best_model.joblib"
        ),
    }


# ─── Feature Translation ─────────────────────────────────────────────────────

def _get_live_system_metrics() -> Dict[str, float]:
    """Fetch live CPU and memory usage from psutil."""
    try:
        return {
            "cpu_usage": psutil.cpu_percent(interval=0.1),
            "memory_usage": psutil.virtual_memory().percent,
        }
    except Exception:
        return {"cpu_usage": 0.0, "memory_usage": 0.0}


def translate_request_to_ml_features(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Translate a backend prediction request dict into the ML module's
    behavioral feature format.

    Backend fields           →  ML feature
    ─────────────────────────────────────────────────────────────────
    entropy                  →  entropy          (direct)
    rapid_changes / 10       →  files_modified_per_sec
    len(extensions_modified) →  extension_changes
    event_type == "renamed"  →  rename_operations  (20 if true)
    event_type == "deleted"  →  files_deleted      (20 if true)
    file_size (log scaled)   →  disk_io
    psutil live              →  cpu_usage, memory_usage
    defaults                 →  everything else
    """
    event_type = (data.get("event_type") or "").lower()
    extensions_modified = data.get("extensions_modified") or []
    rapid_changes = float(data.get("rapid_changes") or 0)
    file_size = float(data.get("file_size") or 0)
    entropy = float(data.get("entropy") or 0.0)

    # Live system metrics
    sys_metrics = _get_live_system_metrics()

    # Disk I/O proxy: log-scale of file size
    import math
    disk_io = math.log1p(file_size) * 1000 if file_size > 0 else 500.0

    features: Dict[str, float] = {
        "files_modified_per_sec": rapid_changes / 10.0,
        "files_created": 1.0 if event_type == "created" else 0.0,
        "files_deleted": 20.0 if event_type == "deleted" else 0.0,
        "rename_operations": 20.0 if event_type == "renamed" else 0.0,
        "read_operations": 10.0 if event_type in ("opened", "read") else 2.0,
        "write_operations": 10.0 if event_type == "modified" else 1.0,
        "entropy": entropy,
        "cpu_usage": sys_metrics["cpu_usage"],
        "memory_usage": sys_metrics["memory_usage"],
        "disk_io": disk_io,
        "extension_changes": float(len(set(extensions_modified))),
        "directories_accessed": 1.0,
        "encryption_ratio": min(entropy / 8.0 * 0.5, 1.0) if entropy > 6.5 else 0.02,
    }

    return features


def translate_ml_result_to_backend(
    ml_result: Dict[str, Any],
    original_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Translate ML module prediction result back to the backend's
    PredictionResult format expected by PredictionService.
    """
    from utils.helpers import generate_id
    from datetime import datetime

    risk_level = ml_result.get("risk_level", "LOW")
    probability = ml_result.get("probability", 0.0)
    is_ransomware = ml_result.get("prediction", 0) == 1

    # Map ML risk_level → backend threat_level
    level_map = {
        "LOW": "low",
        "MEDIUM": "medium",
        "HIGH": "high",
        "CRITICAL": "critical",
    }
    threat_level = level_map.get(risk_level, "safe")
    if not is_ransomware and probability < 0.3:
        threat_level = "safe"

    # Build recommended action
    action_map = {
        "critical": "IMMEDIATELY quarantine file and terminate associated process. Isolate system from network.",
        "high": "Quarantine file immediately. Investigate associated process and network connections.",
        "medium": "Monitor file and associated process closely. Consider quarantine if behavior continues.",
        "low": "Log and monitor. No immediate action required.",
        "safe": "No action required. File appears safe.",
    }

    # Combine ML reasons + MITRE techniques as indicators
    reasons = ml_result.get("reasons", [])
    mitre = ml_result.get("mitre_techniques", [])
    indicators = list(reasons)
    for t in mitre:
        indicators.append(
            f"MITRE {t.get('technique_id', '')}: {t.get('technique_name', '')} ({t.get('tactic', '')})"
        )

    return {
        "prediction_id": generate_id(),
        "file_path": original_data.get("file_path", ""),
        "file_name": original_data.get("file_name", "") or os.path.basename(
            original_data.get("file_path", "")
        ),
        "threat_level": threat_level,
        "confidence": ml_result.get("confidence", 0.0),
        "is_ransomware": is_ransomware,
        "risk_score": round(ml_result.get("risk_score", 0.0) * 100, 2),
        "features_analyzed": translate_request_to_ml_features(original_data),
        "indicators": indicators,
        "recommended_action": action_map.get(threat_level, action_map["safe"]),
        "model_version": "2.0.0-ml",
        "model_type": "ml",
        "ml_details": {
            "probability": ml_result.get("probability"),
            "risk_level": risk_level,
            "model_used": ml_result.get("model_used"),
            "shap_explanation": ml_result.get("shap_explanation"),
            "mitre_techniques": mitre,
            "alert": ml_result.get("alert", False),
            "high_risk": ml_result.get("high_risk", False),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─── Direct ML Prediction ─────────────────────────────────────────────────────

def predict_with_ml(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Run a prediction using the ML module.

    Args:
        data: Backend prediction request dict

    Returns:
        Translated backend-format result, or None if ML unavailable.
    """
    predictor = get_ml_predictor()
    if predictor is None:
        return None

    try:
        ml_features = translate_request_to_ml_features(data)
        ml_result = predictor.predict(ml_features)
        return translate_ml_result_to_backend(ml_result, data)
    except Exception as e:
        logger.error(f"ML prediction error: {e}", exc_info=True)
        return None


def predict_from_features(features: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """
    Run a direct ML prediction from raw behavioral features.
    Used by the /ml/predict-features endpoint.

    Args:
        features: ML behavioral feature dict

    Returns:
        Raw ML result dict, or None if ML unavailable.
    """
    predictor = get_ml_predictor()
    if predictor is None:
        return None

    try:
        return predictor.predict(features)
    except Exception as e:
        logger.error(f"ML direct predict error: {e}", exc_info=True)
        return None
