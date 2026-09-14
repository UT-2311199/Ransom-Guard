import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional

from database.connection import get_collection
from models.ml_model import get_detector
from services.process_service import ProcessService
from utils.logger import setup_logger
from utils.helpers import (
    get_file_name,
    get_file_extension,
    get_file_size,
    generate_id,
    sanitize_path,
)

logger = setup_logger("prediction_service", "logs/prediction.log")

QUARANTINE_DIR = "quarantine"


class PredictionService:
    """Service for ML prediction, process termination, and file quarantine."""

    def __init__(self):
        self.detector = get_detector()
        self.process_service = ProcessService()

    async def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run ML prediction on file data and store result.

        Args:
            data: Prediction request data

        Returns:
            Prediction result dictionary
        """
        try:
            file_path = sanitize_path(data.get("file_path", ""))
            data["file_path"] = file_path
            data["file_name"] = data.get("file_name") or get_file_name(file_path)
            data["file_extension"] = data.get("file_extension") or get_file_extension(file_path)
            data["file_size"] = data.get("file_size") or get_file_size(file_path)

            # Run prediction
            result = self.detector.predict(data)

            # Store prediction in threat_logs if threat level is not safe
            if result.get("threat_level") not in ["safe"]:
                await self._store_threat_log(result, data)

            # Store all predictions in system_logs
            await self._store_prediction_log(result)

            logger.info(
                f"Prediction stored | ID: {result['prediction_id']} | "
                f"Threat: {result['threat_level']}"
            )

            return result

        except Exception as e:
            logger.error(f"Prediction service error: {e}")
            raise

    async def _store_threat_log(self, result: Dict, original_data: Dict):
        """Store threat in threat_logs collection."""
        try:
            collection = get_collection("threat_logs")
            threat_doc = {
                "threat_id": result["prediction_id"],
                "file_path": result["file_path"],
                "file_name": result["file_name"],
                "file_extension": original_data.get("file_extension", ""),
                "threat_level": result["threat_level"],
                "confidence": result["confidence"],
                "risk_score": result["risk_score"],
                "is_ransomware": result["is_ransomware"],
                "indicators": result["indicators"],
                "process_name": original_data.get("process_name"),
                "process_id": original_data.get("process_id"),
                "event_type": original_data.get("event_type"),
                "status": "active",
                "recommended_action": result["recommended_action"],
                "action_taken": None,
                "features": result["features_analyzed"],
                "timestamp": datetime.utcnow(),
                "resolved_at": None,
                "notes": None,
            }
            await collection.insert_one(threat_doc)
        except Exception as e:
            logger.error(f"Error storing threat log: {e}")

    async def _store_prediction_log(self, result: Dict):
        """Store all predictions in system_logs."""
        try:
            collection = get_collection("system_logs")
            log_doc = {
                "log_id": generate_id(),
                "log_type": "prediction",
                "prediction_id": result["prediction_id"],
                "file_path": result["file_path"],
                "file_name": result["file_name"],
                "threat_level": result["threat_level"],
                "is_ransomware": result["is_ransomware"],
                "confidence": result["confidence"],
                "risk_score": result["risk_score"],
                "timestamp": datetime.utcnow(),
            }
            await collection.insert_one(log_doc)
        except Exception as e:
            logger.error(f"Error storing prediction log: {e}")

    async def terminate_process(
        self, pid: int, reason: Optional[str] = None, force: bool = False
    ) -> Dict[str, Any]:
        """
        Terminate a process and log the action.

        Args:
            pid: Process ID
            reason: Reason for termination
            force: Force kill

        Returns:
            Termination result dictionary
        """
        try:
            result = self.process_service.terminate(pid, force=force)

            # Log termination
            await self._log_termination(pid, reason, result)

            return result

        except Exception as e:
            logger.error(f"Error terminating process {pid}: {e}")
            raise

    async def _log_termination(self, pid: int, reason: Optional[str], result: Dict):
        """Log process termination to database."""
        try:
            collection = get_collection("system_logs")
            log_doc = {
                "log_id": generate_id(),
                "log_type": "process_termination",
                "pid": pid,
                "reason": reason,
                "success": result.get("success"),
                "process_name": result.get("process_name"),
                "action": result.get("action"),
                "error": result.get("error"),
                "timestamp": datetime.utcnow(),
            }
            await collection.insert_one(log_doc)
        except Exception as e:
            logger.error(f"Error logging termination: {e}")

    async def quarantine_file(
        self,
        file_path: str,
        threat_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Move a file to the quarantine directory.

        Args:
            file_path: Path to file
            threat_id: Associated threat log ID
            reason: Reason for quarantine

        Returns:
            Quarantine result dictionary
        """
        try:
            file_path = sanitize_path(file_path)

            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "File does not exist",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Create quarantine directory
            os.makedirs(QUARANTINE_DIR, exist_ok=True)

            # Create unique quarantine name
            file_name = get_file_name(file_path)
            quarantine_name = f"{generate_id()}_{file_name}.quarantine"
            quarantine_path = os.path.join(QUARANTINE_DIR, quarantine_name)

            # Move file to quarantine
            shutil.move(file_path, quarantine_path)

            result = {
                "success": True,
                "original_path": file_path,
                "quarantine_path": quarantine_path,
                "file_name": file_name,
                "reason": reason,
                "threat_id": threat_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Update threat log if provided
            if threat_id:
                await self._update_threat_status(
                    threat_id, "quarantined", f"File quarantined: {quarantine_path}"
                )

            # Log quarantine action
            await self._log_quarantine(result)

            logger.warning(f"File quarantined: {file_path} -> {quarantine_path}")
            return result

        except PermissionError as e:
            logger.error(f"Permission denied quarantining {file_path}: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": f"Permission denied: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error quarantining file {file_path}: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _update_threat_status(
        self, threat_id: str, status: str, action_taken: str
    ):
        """Update threat log status."""
        try:
            collection = get_collection("threat_logs")
            await collection.update_one(
                {"threat_id": threat_id},
                {
                    "$set": {
                        "status": status,
                        "action_taken": action_taken,
                        "resolved_at": datetime.utcnow(),
                    }
                },
            )
        except Exception as e:
            logger.error(f"Error updating threat status: {e}")

    async def _log_quarantine(self, result: Dict):
        """Log quarantine action to database."""
        try:
            collection = get_collection("system_logs")
            log_doc = {
                "log_id": generate_id(),
                "log_type": "quarantine",
                **result,
                "timestamp": datetime.utcnow(),
            }
            await collection.insert_one(log_doc)
        except Exception as e:
            logger.error(f"Error logging quarantine: {e}")


def get_prediction_service() -> PredictionService:
    return PredictionService()