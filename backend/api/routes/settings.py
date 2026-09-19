from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from database.connection import get_collection
from schemas.settings import AppSettings, SettingsUpdateRequest
from utils.logger import setup_logger

logger = setup_logger("routes.settings", "logs/app.log")

router = APIRouter()

# Default settings
DEFAULT_SETTINGS = {
    "monitor": {
        "watch_path": "/home",
        "enabled": True,
        "recursive": True,
        "excluded_paths": ["/proc", "/sys", "/dev"],
        "file_extensions_whitelist": [],
    },
    "alerts": {
        "enable_alerts": True,
        "email_alerts": True,
        "alert_email": "admin@company.com",
        "threat_threshold": 0.7,
        "auto_quarantine": False,
        "auto_terminate": False,
        "alert_on_critical": True,
        "alert_on_high": True,
        "alert_on_medium": False,
    },
    "ml": {
        "model_path": "models/ransomware_detector.joblib",
        "confidence_threshold": 0.6,
        "feature_extraction_enabled": True,
        "entropy_analysis": True,
        "behavioral_analysis": True,
    },
    "system": {
        "log_retention_days": 30,
        "report_retention_days": 90,
        "max_log_size_mb": 100,
        "timezone": "UTC",
        "enable_system_monitoring": True,
        "process_scan_interval": 5,
    },
}


@router.get("/settings", summary="Get current settings")
async def get_settings():
    """
    Retrieve current application settings.
    Returns default settings if none have been configured.
    """
    try:
        collection = get_collection("settings")

        # Try to get stored settings
        stored = await collection.find_one({"key": "app_settings"})

        if stored:
            stored.pop("_id", None)
            stored.pop("key", None)
            settings_data = stored.get("value", DEFAULT_SETTINGS)
        else:
            settings_data = DEFAULT_SETTINGS

        return {
            "success": True,
            "settings": settings_data,
            "message": "Settings retrieved successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"GET /settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings", summary="Update application settings")
async def update_settings(request: SettingsUpdateRequest):
    """
    Update application settings.

    Only provided fields will be updated. Other fields retain their current values.
    """
    try:
        collection = get_collection("settings")

        # Get current settings
        stored = await collection.find_one({"key": "app_settings"})
        current = stored.get("value", DEFAULT_SETTINGS) if stored else DEFAULT_SETTINGS

        # Merge updates
        update_data = request.dict(exclude_none=True)

        for section, values in update_data.items():
            if section in current and isinstance(values, dict):
                current[section].update(values)
            elif values is not None:
                current[section] = values

        current["updated_at"] = datetime.utcnow().isoformat()

        # Upsert settings
        await collection.update_one(
            {"key": "app_settings"},
            {"$set": {"key": "app_settings", "value": current, "updated_at": datetime.utcnow()}},
            upsert=True,
        )

        # Log settings change
        logs_collection = get_collection("system_logs")
        await logs_collection.insert_one(
            {
                "log_type": "settings_update",
                "changes": update_data,
                "timestamp": datetime.utcnow(),
            }
        )

        logger.info(f"Settings updated: {list(update_data.keys())}")

        return {
            "success": True,
            "settings": current,
            "message": "Settings updated successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"POST /settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settings/reset", summary="Reset settings to defaults")
async def reset_settings():
    """
    Reset all settings to their default values.
    """
    try:
        collection = get_collection("settings")

        await collection.update_one(
            {"key": "app_settings"},
            {
                "$set": {
                    "key": "app_settings",
                    "value": DEFAULT_SETTINGS,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

        logger.info("Settings reset to defaults")

        return {
            "success": True,
            "settings": DEFAULT_SETTINGS,
            "message": "Settings reset to defaults successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"DELETE /settings/reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/test-email", summary="Send a test alert email")
async def send_test_email(req: dict):
    """
    Dispatch a test security alert email to verify notification settings.
    """
    email_to = req.get("email") or "admin@company.com"
    try:
        from utils.email_service import send_test_security_email
        res = send_test_security_email(email_to)
        return {
            "success": res.get("success", True),
            "mode": res.get("mode", "simulated"),
            "message": res.get("message", f"Test email dispatched to {email_to}"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"POST /settings/test-email error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to dispatch test email: {e}")