# ml/predictor/predictor.py

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ml.feature_extractor.engineer import FeatureEngineer
from ml.models.model_registry import ModelRegistry
from ml.evaluation.evaluator import ModelEvaluator
from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, MonitoringConfig, RiskConfig
from ml.utils.mitre import MITREMapper, MITRETechnique

logger = get_logger(__name__)


# Risk level labels
RISK_LEVELS = {
    "LOW": (0.0, 0.30),
    "MEDIUM": (0.30, 0.60),
    "HIGH": (0.60, 0.85),
    "CRITICAL": (0.85, 1.0),
}


class RansomwarePredictor:
    """
    Live ransomware prediction engine.
    Loads a trained model and provides real-time predictions with:
    - Probability scores
    - Risk levels
    - SHAP-based explanations
    - MITRE ATT&CK mapping
    """

    def __init__(
        self,
        monitoring_config: Optional[MonitoringConfig] = None,
        risk_config: Optional[RiskConfig] = None,
        model_registry: Optional[ModelRegistry] = None,
    ):
        self.monitoring_config = monitoring_config or CONFIG.monitoring
        self.risk_config = risk_config or CONFIG.risk
        self.registry = model_registry or ModelRegistry()
        self.evaluator = ModelEvaluator()
        self.mitre_mapper = MITREMapper()

        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.engineer: Optional[FeatureEngineer] = None
        self.feature_names: Optional[List[str]] = None
        self.model_name: Optional[str] = None

        self._loaded = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def load(self) -> None:
        """
        Load the best trained model, scaler, and metadata.
        Must be called before predict().
        """
        logger.info("Loading RansomwarePredictor...")

        if not self.registry.is_trained():
            raise FileNotFoundError(
                "No trained model found. Run the training pipeline first."
            )

        self.model = self.registry.load_best_model()
        self.scaler = self.registry.load_scaler()
        self.feature_names = self.registry.get_feature_names()

        metadata = self.registry.load_metadata()
        if metadata:
            self.model_name = metadata.get("best_model_name", "Unknown")
            logger.info(f"Loaded model: {self.model_name}")
            logger.info(f"Features: {len(self.feature_names or [])} features")

        # Reconstruct FeatureEngineer with fitted scaler
        self.engineer = FeatureEngineer()
        self.engineer.scaler = self.scaler
        self.engineer._fitted = True

        self._loaded = True
        logger.info("RansomwarePredictor ready.")

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Run prediction on a feature dictionary.

        Args:
            features: Dictionary of feature_name -> value

        Returns:
            Full prediction result with prediction, probability,
            confidence, risk_score, risk_level, reasons, and MITRE mapping.
        """
        self._ensure_loaded()

        # Build DataFrame from features
        df = self._build_feature_dataframe(features)

        # Run model inference
        prediction = int(self.model.predict(df)[0])
        proba_array = self.model.predict_proba(df)[0]
        probability = float(proba_array[1])  # probability of ransomware

        # Compute risk score
        risk_score = self._compute_risk_score(features, probability)

        # Determine risk level
        risk_level = self._get_risk_level(risk_score)

        # Confidence (distance from 0.5 decision boundary)
        confidence = self._compute_confidence(probability)

        # Build explanations
        reasons = self._build_reasons(features, probability, risk_score)

        # SHAP-based explanation
        shap_explanation = self._get_shap_explanation(df)

        # MITRE ATT&CK mapping
        mitre_techniques = self.mitre_mapper.map_features_to_techniques(
            features=features,
            prediction=prediction,
            probability=probability,
        )
        mitre_list = [
            {
                "technique_id": t.technique_id,
                "technique_name": t.technique_name,
                "tactic": t.tactic,
                "reference": t.reference_url,
            }
            for t in mitre_techniques
        ]

        result = {
            "prediction": prediction,
            "label": "RANSOMWARE" if prediction == 1 else "BENIGN",
            "probability": round(probability, 4),
            "confidence": round(confidence, 4),
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "reasons": reasons,
            "shap_explanation": shap_explanation,
            "mitre_techniques": mitre_list,
            "model_used": self.model_name,
            "alert": risk_score >= self.monitoring_config.alert_threshold,
            "high_risk": risk_score >= self.monitoring_config.high_risk_threshold,
        }

        self._log_prediction(result)
        return result

    def predict_batch(
        self, features_list: List[Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Run predictions on a list of feature dictionaries.

        Args:
            features_list: List of feature dictionaries

        Returns:
            List of prediction result dictionaries
        """
        self._ensure_loaded()
        return [self.predict(f) for f in features_list]

    # ------------------------------------------------------------------
    # Risk Scoring
    # ------------------------------------------------------------------

    def _compute_risk_score(
        self, features: Dict[str, float], model_probability: float
    ) -> float:
        """
        Compute a composite risk score combining model probability
        with individual feature signals.

        Returns:
            Risk score in [0, 1]
        """
        weights = self.risk_config.risk_weights

        # Model probability component
        model_score = model_probability

        # Entropy component (normalized to 0-8 scale)
        entropy_raw = features.get("entropy", 0)
        entropy_score = min(entropy_raw / 8.0, 1.0)

        # Encryption ratio component
        encryption_score = min(features.get("encryption_ratio", 0), 1.0)

        # File activity component
        mod_rate = features.get("files_modified_per_sec", 0)
        renames = features.get("rename_operations", 0)
        deletes = features.get("files_deleted", 0)
        file_activity = min((mod_rate / 200.0 + renames / 200.0 + deletes / 500.0) / 3.0, 1.0)

        # Process/system component
        cpu = features.get("cpu_usage", 0) / 100.0
        mem = features.get("memory_usage", 0) / 100.0
        process_score = (cpu + mem) / 2.0

        risk_score = (
            weights["model_probability"] * model_score
            + weights["entropy_score"] * entropy_score
            + weights["encryption_ratio_score"] * encryption_score
            + weights["file_activity_score"] * file_activity
            + weights["process_score"] * process_score
        )

        return min(float(risk_score), 1.0)

    def _get_risk_level(self, risk_score: float) -> str:
        """Map a risk score to a categorical risk level."""
        rc = self.risk_config
        if risk_score <= rc.low_risk_max:
            return "LOW"
        elif risk_score <= rc.medium_risk_max:
            return "MEDIUM"
        elif risk_score <= rc.high_risk_max:
            return "HIGH"
        else:
            return "CRITICAL"

    def _compute_confidence(self, probability: float) -> float:
        """
        Compute prediction confidence as distance from decision boundary (0.5).
        Returns value in [0, 1] where 1 = perfectly confident.
        """
        return abs(probability - 0.5) * 2.0

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def _build_reasons(
        self,
        features: Dict[str, float],
        probability: float,
        risk_score: float,
    ) -> List[str]:
        """
        Generate human-readable reasons for the prediction.

        Returns:
            List of reason strings explaining the detection
        """
        reasons = []

        if features.get("entropy", 0) >= 7.0:
            reasons.append(
                f"High file entropy ({features['entropy']:.2f}/8.0) — "
                "consistent with encrypted file content."
            )

        if features.get("encryption_ratio", 0) >= 0.5:
            reasons.append(
                f"Elevated encryption ratio ({features['encryption_ratio']:.2%}) — "
                "large proportion of files show encryption characteristics."
            )

        if features.get("files_modified_per_sec", 0) >= 50:
            reasons.append(
                f"Mass file modification rate ({features['files_modified_per_sec']:.0f} files/sec) — "
                "ransomware typically modifies files at high speed."
            )

        if features.get("rename_operations", 0) >= 50:
            reasons.append(
                f"High rename activity ({features['rename_operations']:.0f} renames) — "
                "ransomware often renames files with new extensions."
            )

        if features.get("extension_changes", 0) >= 20:
            reasons.append(
                f"Suspicious extension changes ({features['extension_changes']:.0f}) — "
                "file extensions being altered, a ransomware indicator."
            )

        if features.get("files_deleted", 0) >= 100:
            reasons.append(
                f"High file deletion rate ({features['files_deleted']:.0f} files) — "
                "ransomware may delete originals after encryption."
            )

        if features.get("cpu_usage", 0) >= 80:
            reasons.append(
                f"High CPU usage ({features['cpu_usage']:.1f}%) — "
                "encryption is computationally intensive."
            )

        if features.get("directories_accessed", 0) >= 100:
            reasons.append(
                f"Wide directory traversal ({features['directories_accessed']:.0f} dirs) — "
                "ransomware scans all accessible directories."
            )

        if not reasons and probability >= 0.5:
            reasons.append(
                f"Model confidence of {probability:.2%} suggests ransomware-like "
                "behavioral pattern across multiple features."
            )

        return reasons

    def _get_shap_explanation(
        self, df: pd.DataFrame
    ) -> Optional[Dict[str, float]]:
        """Get SHAP feature contributions for this prediction."""
        try:
            shap_exp = self.evaluator.get_shap_explanation(self.model, df)
            if shap_exp:
                # Sort by absolute importance
                return dict(
                    sorted(shap_exp.items(), key=lambda x: abs(x[1]), reverse=True)
                )
        except Exception as exc:
            logger.debug(f"SHAP explanation skipped: {exc}")
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_feature_dataframe(self, features: Dict[str, float]) -> pd.DataFrame:
        """
        Convert a feature dictionary to a scaled DataFrame
        ready for model inference.
        """
        # Use engineer to add derived features and scale
        df = self.engineer.transform_dict(features)
        return df

    def _ensure_loaded(self) -> None:
        """Raise if predictor has not been loaded."""
        if not self._loaded:
            raise RuntimeError(
                "Predictor not loaded. Call predictor.load() first."
            )

    def _log_prediction(self, result: Dict[str, Any]) -> None:
        """Log the prediction result."""
        level = result["risk_level"]
        label = result["label"]
        prob = result["probability"]
        risk = result["risk_score"]

        if result["high_risk"]:
            logger.critical(
                f"[{level}] {label} | prob={prob:.4f} | risk={risk:.4f}"
            )
        elif result["alert"]:
            logger.warning(
                f"[{level}] {label} | prob={prob:.4f} | risk={risk:.4f}"
            )
        else:
            logger.debug(
                f"[{level}] {label} | prob={prob:.4f} | risk={risk:.4f}"
            )