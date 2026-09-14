# ml/models/model_registry.py

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, ModelConfig

logger = get_logger(__name__)


class ModelRegistry:
    """
    Handles saving, loading, and versioning of trained models,
    scalers, and associated metadata.
    """

    def __init__(self, model_config: Optional[ModelConfig] = None):
        self.config = model_config or CONFIG.model
        os.makedirs(self.config.model_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Save Methods
    # ------------------------------------------------------------------

    def save_all(
        self,
        rf_model: Any,
        xgb_model: Any,
        best_model: Any,
        best_model_name: str,
        scaler: Any,
        feature_names: List[str],
        rf_metrics: Dict[str, Any],
        xgb_metrics: Dict[str, Any],
        dataset_stats: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Save all model artifacts and metadata.

        Returns:
            Dictionary of artifact_name -> saved_path
        """
        saved_paths = {}

        # Save Random Forest
        rf_path = self._save_artifact(rf_model, self.config.rf_model_filename)
        saved_paths["random_forest"] = rf_path

        # Save XGBoost
        xgb_path = self._save_artifact(xgb_model, self.config.xgb_model_filename)
        saved_paths["xgboost"] = xgb_path

        # Save Best Model
        best_path = self._save_artifact(best_model, self.config.best_model_filename)
        saved_paths["best_model"] = best_path

        # Save Scaler
        scaler_path = self._save_artifact(scaler, self.config.scaler_filename)
        saved_paths["scaler"] = scaler_path

        # Save Metadata
        metadata = self._build_metadata(
            best_model_name=best_model_name,
            feature_names=feature_names,
            rf_metrics=rf_metrics,
            xgb_metrics=xgb_metrics,
            dataset_stats=dataset_stats,
        )
        meta_path = self._save_metadata(metadata)
        saved_paths["metadata"] = meta_path

        logger.info(f"All artifacts saved to: {self.config.model_dir}")
        return saved_paths

    def save_model(self, model: Any, filename: str) -> str:
        """Save a single model artifact."""
        return self._save_artifact(model, filename)

    # ------------------------------------------------------------------
    # Load Methods
    # ------------------------------------------------------------------

    def load_best_model(self) -> Any:
        """Load the best trained model."""
        path = os.path.join(self.config.model_dir, self.config.best_model_filename)
        return self._load_artifact(path, "best model")

    def load_scaler(self) -> Any:
        """Load the fitted feature scaler."""
        path = os.path.join(self.config.model_dir, self.config.scaler_filename)
        return self._load_artifact(path, "scaler")

    def load_random_forest(self) -> Any:
        """Load the Random Forest model."""
        path = os.path.join(self.config.model_dir, self.config.rf_model_filename)
        return self._load_artifact(path, "random forest")

    def load_xgboost(self) -> Any:
        """Load the XGBoost model."""
        path = os.path.join(self.config.model_dir, self.config.xgb_model_filename)
        return self._load_artifact(path, "xgboost")

    def load_metadata(self) -> Optional[Dict[str, Any]]:
        """Load model metadata from JSON."""
        path = os.path.join(self.config.model_dir, self.config.metadata_filename)
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Metadata file not found: {path}")
            return None
        except json.JSONDecodeError as exc:
            logger.error(f"Metadata JSON parse error: {exc}")
            return None

    def is_trained(self) -> bool:
        """Check whether a trained best model exists."""
        path = os.path.join(self.config.model_dir, self.config.best_model_filename)
        return os.path.exists(path)

    def get_feature_names(self) -> Optional[List[str]]:
        """Load feature names from saved metadata."""
        metadata = self.load_metadata()
        if metadata:
            return metadata.get("feature_names")
        return None

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _save_artifact(self, artifact: Any, filename: str) -> str:
        """Serialize and save an artifact with joblib."""
        path = os.path.join(self.config.model_dir, filename)
        joblib.dump(artifact, path, compress=3)
        size_kb = os.path.getsize(path) / 1024
        logger.info(f"Saved: {filename} ({size_kb:.1f} KB)")
        return path

    def _load_artifact(self, path: str, name: str) -> Any:
        """Load a joblib-serialized artifact."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} not found at: {path}")
        artifact = joblib.load(path)
        logger.info(f"Loaded {name} from: {path}")
        return artifact

    def _build_metadata(
        self,
        best_model_name: str,
        feature_names: List[str],
        rf_metrics: Dict[str, Any],
        xgb_metrics: Dict[str, Any],
        dataset_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build the metadata dictionary for persistence."""
        # Remove non-serializable items from metrics
        def clean_metrics(m: Dict) -> Dict:
            return {
                k: v for k, v in m.items()
                if isinstance(v, (int, float, str, list, dict, bool, type(None)))
                and k != "classification_report"
            }

        return {
            "version": "1.0.0",
            "trained_at": datetime.utcnow().isoformat() + "Z",
            "best_model_name": best_model_name,
            "feature_names": feature_names,
            "feature_count": len(feature_names),
            "rf_metrics": clean_metrics(rf_metrics),
            "xgb_metrics": clean_metrics(xgb_metrics),
            "dataset": {
                "total_samples": dataset_stats.get("total_samples"),
                "ransomware_samples": dataset_stats.get("ransomware_samples"),
                "benign_samples": dataset_stats.get("benign_samples"),
                "class_balance": dataset_stats.get("class_balance"),
            },
            "model_files": {
                "best_model": self.config.best_model_filename,
                "random_forest": self.config.rf_model_filename,
                "xgboost": self.config.xgb_model_filename,
                "scaler": self.config.scaler_filename,
            },
        }

    def _save_metadata(self, metadata: Dict[str, Any]) -> str:
        """Serialize metadata to JSON."""
        path = os.path.join(self.config.model_dir, self.config.metadata_filename)
        with open(path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.info(f"Metadata saved: {path}")
        return path