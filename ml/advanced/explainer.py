# ml/advanced/explainer.py

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ml.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not available. Install with: pip install shap")


class ExplainabilityEngine:
    """
    Provides SHAP-based explanations for individual predictions
    and global feature importance analysis.
    Supports both Random Forest and XGBoost models.
    """

    def __init__(self, model: Any, feature_names: Optional[List[str]] = None):
        self.model = model
        self.feature_names = feature_names
        self._explainer: Optional[Any] = None
        self._background_data: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def initialize(self, background_data: pd.DataFrame, max_background: int = 200) -> None:
        """
        Initialize the SHAP explainer with background data.

        Args:
            background_data: DataFrame of representative samples (training data)
            max_background: Max background samples for efficiency
        """
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not available. Explanations will be limited.")
            return

        try:
            sample = background_data.sample(
                min(max_background, len(background_data)), random_state=42
            )
            self._background_data = sample
            self._explainer = shap.TreeExplainer(self.model, sample)
            logger.info(
                f"SHAP explainer initialized with {len(sample)} background samples."
            )
        except Exception as exc:
            logger.error(f"SHAP explainer initialization failed: {exc}")

    # ------------------------------------------------------------------
    # Individual Explanations
    # ------------------------------------------------------------------

    def explain_prediction(
        self, X: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Explain a single prediction using SHAP values.

        Args:
            X: Single-row feature DataFrame

        Returns:
            Dictionary with shap_values, top_features, and summary
        """
        if not SHAP_AVAILABLE or self._explainer is None:
            return self._fallback_explanation(X)

        try:
            shap_values = self._explainer.shap_values(X)

            # For binary classification: use class 1 (ransomware) SHAP values
            if isinstance(shap_values, list):
                sv = shap_values[1][0]
            else:
                sv = shap_values[0]

            feature_names = (
                self.feature_names or X.columns.tolist()
            )
            contributions = dict(zip(feature_names, sv))

            # Sort by absolute contribution
            sorted_contributions = dict(
                sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
            )

            # Build top features list
            top_features = [
                {
                    "feature": fname,
                    "shap_value": round(float(fval), 4),
                    "direction": "increases risk" if fval > 0 else "decreases risk",
                    "magnitude": "high" if abs(fval) > 0.3
                    else "medium" if abs(fval) > 0.1
                    else "low",
                }
                for fname, fval in list(sorted_contributions.items())[:10]
            ]

            # Base value (expected model output)
            base_value = float(
                self._explainer.expected_value[1]
                if isinstance(self._explainer.expected_value, (list, np.ndarray))
                else self._explainer.expected_value
            )

            return {
                "method": "SHAP TreeExplainer",
                "base_value": round(base_value, 4),
                "shap_contributions": sorted_contributions,
                "top_features": top_features,
                "summary": self._format_explanation_summary(top_features),
            }

        except Exception as exc:
            logger.error(f"SHAP explanation failed: {exc}")
            return self._fallback_explanation(X)

    def explain_global(
        self, X: pd.DataFrame, max_samples: int = 500
    ) -> Dict[str, Any]:
        """
        Compute global SHAP-based feature importance.

        Args:
            X: Feature DataFrame (subset of training/test data)
            max_samples: Max samples for computation

        Returns:
            Dictionary with global feature importance rankings
        """
        if not SHAP_AVAILABLE or self._explainer is None:
            return self._fallback_global_importance()

        try:
            X_sample = X.sample(min(max_samples, len(X)), random_state=42)
            shap_values = self._explainer.shap_values(X_sample)

            sv = shap_values[1] if isinstance(shap_values, list) else shap_values
            mean_abs_shap = np.abs(sv).mean(axis=0)

            feature_names = self.feature_names or X.columns.tolist()
            global_importance = dict(
                sorted(
                    zip(feature_names, mean_abs_shap),
                    key=lambda x: x[1],
                    reverse=True,
                )
            )

            return {
                "method": "SHAP Global Importance (mean |SHAP value|)",
                "feature_importance": {
                    k: round(float(v), 6) for k, v in global_importance.items()
                },
                "top_5_features": list(global_importance.keys())[:5],
            }

        except Exception as exc:
            logger.error(f"Global SHAP explanation failed: {exc}")
            return self._fallback_global_importance()

    # ------------------------------------------------------------------
    # Feature Contribution Analysis
    # ------------------------------------------------------------------

    def analyze_threshold_breach(
        self, features: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Identify which features are breaching ransomware thresholds.

        Args:
            features: Feature dictionary

        Returns:
            List of breached feature details with severity
        """
        THRESHOLDS = {
            "entropy": {"threshold": 7.0, "max": 8.0, "label": "File Entropy"},
            "encryption_ratio": {"threshold": 0.5, "max": 1.0, "label": "Encryption Ratio"},
            "files_modified_per_sec": {"threshold": 50, "max": 500, "label": "Files Modified/sec"},
            "rename_operations": {"threshold": 50, "max": 500, "label": "Rename Operations"},
            "files_deleted": {"threshold": 100, "max": 1000, "label": "Files Deleted"},
            "extension_changes": {"threshold": 20, "max": 200, "label": "Extension Changes"},
            "directories_accessed": {"threshold": 100, "max": 1000, "label": "Directories Accessed"},
            "cpu_usage": {"threshold": 80, "max": 100, "label": "CPU Usage (%)"},
        }

        breached = []
        for feature, 