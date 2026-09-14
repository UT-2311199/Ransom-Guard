# ml/evaluation/evaluator.py

import os
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    ConfusionMatrixDisplay,
)

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG

logger = get_logger(__name__)

PLOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plots")
os.makedirs(PLOT_DIR, exist_ok=True)


class ModelEvaluator:
    """
    Comprehensive evaluation of ransomware detection models.
    Computes classification metrics, plots ROC curves, confusion matrices,
    feature importance charts, and SHAP explainability plots.
    """

    def __init__(self, plot_dir: Optional[str] = None):
        self.plot_dir = plot_dir or PLOT_DIR
        os.makedirs(self.plot_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        model_name: str = "Model",
        save_plots: bool = True,
    ) -> Dict[str, Any]:
        """
        Full evaluation of a trained model.

        Args:
            model: Fitted sklearn-compatible model
            X_test: Test features
            y_test: True labels
            model_name: Display name for the model
            save_plots: Whether to save plots to disk

        Returns:
            Dictionary of all computed metrics
        """
        logger.info(f"Evaluating [{model_name}] on {len(X_test)} test samples...")

        y_pred = model.predict(X_test)
        y_proba = self._get_probabilities(model, X_test)

        metrics = self._compute_metrics(y_test, y_pred, y_proba, model_name)

        if save_plots:
            self._plot_confusion_matrix(y_test, y_pred, model_name)
            if y_proba is not None:
                self._plot_roc_curve(y_test, y_proba, model_name, metrics.get("roc_auc", 0))
            self._plot_feature_importance(model, X_test, model_name)
            if SHAP_AVAILABLE:
                self._plot_shap_summary(model, X_test, model_name)

        self._log_metrics(metrics, model_name)
        return metrics

    def compute_shap_values(
        self,
        model: Any,
        X: pd.DataFrame,
        max_samples: int = 500,
    ) -> Optional[Any]:
        """
        Compute SHAP values for model explainability.

        Args:
            model: Fitted model
            X: Feature DataFrame
            max_samples: Max samples to use for SHAP (for performance)

        Returns:
            SHAP values array or None if SHAP unavailable
        """
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not available. Install with: pip install shap")
            return None

        try:
            X_sample = X.sample(min(max_samples, len(X)), random_state=42)
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)
            return shap_values
        except Exception as exc:
            logger.error(f"SHAP computation failed: {exc}")
            return None

    def get_shap_explanation(
        self,
        model: Any,
        X_single: pd.DataFrame,
    ) -> Optional[Dict[str, float]]:
        """
        Get SHAP explanation for a single prediction instance.

        Args:
            model: Fitted model
            X_single: Single-row DataFrame

        Returns:
            Dictionary of feature_name -> shap_value
        """
        if not SHAP_AVAILABLE:
            return None

        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_single)

            # For binary classification, shap_values[1] = positive class
            if isinstance(shap_values, list):
                values = shap_values[1][0]
            else:
                values = shap_values[0]

            return dict(zip(X_single.columns, values))
        except Exception as exc:
            logger.error(f"Single SHAP explanation failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # Private: Metrics
    # ------------------------------------------------------------------

    def _compute_metrics(
        self,
        y_true: pd.Series,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray],
        model_name: str,
    ) -> Dict[str, Any]:
        """Compute all classification metrics."""
        metrics: Dict[str, Any] = {
            "model_name": model_name,
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
            "classification_report": classification_report(
                y_true, y_pred, target_names=["Benign", "Ransomware"]
            ),
        }

        if y_proba is not None:
            try:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
            except ValueError as exc:
                logger.warning(f"ROC-AUC computation failed: {exc}")
                metrics["roc_auc"] = 0.0
        else:
            metrics["roc_auc"] = 0.0

        return metrics

    # ------------------------------------------------------------------
    # Private: Plotting
    # ------------------------------------------------------------------

    def _plot_confusion_matrix(
        self, y_true: pd.Series, y_pred: np.ndarray, model_name: str
    ) -> None:
        """Save a confusion matrix plot."""
        try:
            cm = confusion_matrix(y_true, y_pred)
            fig, ax = plt.subplots(figsize=(6, 5))
            disp = ConfusionMatrixDisplay(
                confusion_matrix=cm,
                display_labels=["Benign", "Ransomware"],
            )
            disp.plot(ax=ax, cmap="Blues", colorbar=False)
            ax.set_title(f"Confusion Matrix — {model_name}")
            plt.tight_layout()
            path = os.path.join(self.plot_dir, f"confusion_matrix_{model_name}.png")
            plt.savefig(path, dpi=150)
            plt.close(fig)
            logger.info(f"Confusion matrix saved: {path}")
        except Exception as exc:
            logger.error(f"Failed to plot confusion matrix: {exc}")

    def _plot_roc_curve(
        self,
        y_true: pd.Series,
        y_proba: np.ndarray,
        model_name: str,
        roc_auc: float,
    ) -> None:
        """Save a ROC curve plot."""
        try:
            fpr, tpr, _ = roc_curve(y_true, y_proba)
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.plot(fpr, tpr, lw=2, color="steelblue", label=f"AUC = {roc_auc:.4f}")
            ax.plot([0, 1], [0, 1], "k--", lw=1, label="Random")
            ax.set_xlabel("False Positive Rate", fontsize=12)
            ax.set_ylabel("True Positive Rate", fontsize=12)
            ax.set_title(f"ROC Curve — {model_name}", fontsize=14)
            ax.legend(loc="lower right", fontsize=11)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            path = os.path.join(self.plot_dir, f"roc_curve_{model_name}.png")
            plt.savefig(path, dpi=150)
            plt.close(fig)
            logger.info(f"ROC curve saved: {path}")
        except Exception as exc:
            logger.error(f"Failed to plot ROC curve: {exc}")

    def _plot_feature_importance(
        self, model: Any, X_test: pd.DataFrame, model_name: str, top_n: int = 15
    ) -> None:
        """Save a feature importance bar chart."""
        try:
            if not hasattr(model, "feature_importances_"):
                return

            importances = pd.Series(
                model.feature_importances_,
                index=X_test.columns,
            ).sort_values(ascending=True).tail(top_n)

            fig, ax = plt.subplots(figsize=(8, 6))
            colors = plt.cm.RdYlGn(importances.values / importances.values.max())
            importances.plot(kind="barh", ax=ax, color=colors, edgecolor="black", linewidth=0.5)
            ax.set_xlabel("Feature Importance", fontsize=12)
            ax.set_title(f"Top {top_n} Feature Importances — {model_name}", fontsize=14)
            ax.grid(axis="x", alpha=0.3)
            plt.tight_layout()
            path = os.path.join(self.plot_dir, f"feature_importance_{model_name}.png")
            plt.savefig(path, dpi=150)
            plt.close(fig)
            logger.info(f"Feature importance plot saved: {path}")
        except Exception as exc:
            logger.error(f"Failed to plot feature importance: {exc}")

    def _plot_shap_summary(
        self, model: Any, X_test: pd.DataFrame, model_name: str, max_samples: int = 300
    ) -> None:
        """Save a SHAP summary plot."""
        if not SHAP_AVAILABLE:
            return
        try:
            X_sample = X_test.sample(min(max_samples, len(X_test)), random_state=42)
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)

            fig = plt.figure(figsize=(10, 7))

            # For binary classification
            sv = shap_values[1] if isinstance(shap_values, list) else shap_values
            shap.summary_plot(sv, X_sample, show=False, plot_type="bar")

            plt.title(f"SHAP Feature Importance — {model_name}", fontsize=14)
            plt.tight_layout()
            path = os.path.join(self.plot_dir, f"shap_summary_{model_name}.png")
            plt.savefig(path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            logger.info(f"SHAP summary plot saved: {path}")
        except Exception as exc:
            logger.error(f"SHAP plot failed: {exc}")

    # ------------------------------------------------------------------
    # Private: Helpers
    # ------------------------------------------------------------------

    def _get_probabilities(
        self, model: Any, X_test: pd.DataFrame
    ) -> Optional[np.ndarray]:
        """Get positive class probability from model if available."""
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X_test)
            return proba[:, 1]
        return None

    def _log_metrics(self, metrics: Dict[str, Any], model_name: str) -> None:
        """Log evaluation metrics in a formatted table."""
        logger.info(f"\n{'='*50}")
        logger.info(f"  Evaluation Results: {model_name}")
        logger.info(f"{'='*50}")
        logger.info(f"  Accuracy  : {metrics['accuracy']:.4f}")
        logger.info(f"  Precision : {metrics['precision']:.4f}")
        logger.info(f"  Recall    : {metrics['recall']:.4f}")
        logger.info(f"  F1 Score  : {metrics['f1']:.4f}")
        logger.info(f"  ROC-AUC   : {metrics['roc_auc']:.4f}")
        logger.info(f"\n{metrics['classification_report']}")
        logger.info(f"{'='*50}")