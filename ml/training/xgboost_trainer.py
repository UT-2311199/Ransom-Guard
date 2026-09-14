# ml/training/xgboost_trainer.py

from typing import Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score

try:
    from xgboost import XGBClassifier
except ImportError as exc:
    raise ImportError("XGBoost is required: pip install xgboost") from exc

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, XGBoostConfig

logger = get_logger(__name__)


class XGBoostTrainer:
    """
    Trains an XGBoost classifier for ransomware detection.
    Supports standard training, early stopping, and cross-validation.
    """

    def __init__(self, xgb_config: Optional[XGBoostConfig] = None):
        self.config = xgb_config or CONFIG.xgboost
        self.model: Optional[XGBClassifier] = None
        self._feature_names: Optional[list] = None

    def build_model(self, params: Optional[Dict[str, Any]] = None) -> XGBClassifier:
        """
        Instantiate XGBClassifier with config or custom params.

        Args:
            params: Optional parameter overrides

        Returns:
            Unfit XGBClassifier
        """
        base_params = {
            "n_estimators": self.config.n_estimators,
            "max_depth": self.config.max_depth,
            "learning_rate": self.config.learning_rate,
            "subsample": self.config.subsample,
            "colsample_bytree": self.config.colsample_bytree,
            "eval_metric": self.config.eval_metric,
            "random_state": self.config.random_state,
            "n_jobs": self.config.n_jobs,
            "scale_pos_weight": self.config.scale_pos_weight,
            "use_label_encoder": False,
        }
        if params:
            base_params.update(params)

        model = XGBClassifier(**base_params)
        logger.info(f"XGBoost model built with params: {base_params}")
        return model

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        params: Optional[Dict[str, Any]] = None,
        early_stopping_rounds: int = 20,
    ) -> XGBClassifier:
        """
        Fit XGBoost on training data with optional validation set for early stopping.

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Optional validation features
            y_val: Optional validation labels
            params: Optional parameter overrides
            early_stopping_rounds: Rounds without improvement before stopping

        Returns:
            Fitted XGBClassifier
        """
        logger.info(f"Training XGBoost | X_train shape: {X_train.shape}")
        self.model = self.build_model(params)
        self._feature_names = X_train.columns.tolist()

        fit_kwargs: Dict[str, Any] = {}

        if X_val is not None and y_val is not None:
            fit_kwargs["eval_set"] = [(X_val, y_val)]
            fit_kwargs["verbose"] = False
            logger.info("Using validation set with early stopping.")

        self.model.fit(X_train, y_train, **fit_kwargs)

        best_iteration = getattr(self.model, "best_iteration", None)
        if best_iteration is not None:
            logger.info(f"XGBoost best iteration: {best_iteration}")

        logger.info("XGBoost training complete.")
        return self.model

    def cross_validate(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        cv: int = 5,
        scoring: str = "f1",
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """
        Perform k-fold cross-validation.

        Args:
            X: Features
            y: Labels
            cv: Number of folds
            scoring: Sklearn scoring metric
            params: Optional parameter overrides

        Returns:
            Dictionary with mean and std of cross-validation scores
        """
        model = self.build_model(params)
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring, n_jobs=-1)
        result = {
            "cv_mean": float(np.mean(scores)),
            "cv_std": float(np.std(scores)),
            "cv_scores": scores.tolist(),
        }
        logger.info(
            f"XGB Cross-Validation ({cv}-fold, {scoring}): "
            f"mean={result['cv_mean']:.4f} ± {result['cv_std']:.4f}"
        )
        return result

    def get_feature_importances(self) -> Optional[pd.Series]:
        """
        Return feature importances from the fitted model.

        Returns:
            Sorted Series of feature_name -> importance
        """
        if self.model is None:
            logger.warning("Model not yet trained. Call train() first.")
            return None
        if self._feature_names is None:
            return None

        importances = pd.Series(
            self.model.feature_importances_,
            index=self._feature_names,
            name="importance",
        ).sort_values(ascending=False)
        return importances

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Run inference and return class predictions."""
        if self.model is None:
            raise RuntimeError("Model not trained.")
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Run inference and return class probabilities."""
        if self.model is None:
            raise RuntimeError("Model not trained.")
        return self.model.predict_proba(X)