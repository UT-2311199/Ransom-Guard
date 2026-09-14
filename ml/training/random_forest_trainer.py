# ml/training/random_forest_trainer.py

from typing import Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, RandomForestConfig

logger = get_logger(__name__)


class RandomForestTrainer:
    """
    Trains a Random Forest classifier for ransomware detection.
    Supports standard training and cross-validation.
    """

    def __init__(self, rf_config: Optional[RandomForestConfig] = None):
        self.config = rf_config or CONFIG.random_forest
        self.model: Optional[RandomForestClassifier] = None
        self._feature_names: Optional[list] = None

    def build_model(self, params: Optional[Dict[str, Any]] = None) -> RandomForestClassifier:
        """
        Instantiate the RandomForestClassifier with config or custom params.

        Args:
            params: Optional parameter overrides

        Returns:
            Unfit RandomForestClassifier instance
        """
        base_params = {
            "n_estimators": self.config.n_estimators,
            "max_depth": self.config.max_depth,
            "min_samples_split": self.config.min_samples_split,
            "min_samples_leaf": self.config.min_samples_leaf,
            "max_features": self.config.max_features,
            "class_weight": self.config.class_weight,
            "random_state": self.config.random_state,
            "n_jobs": self.config.n_jobs,
        }
        if params:
            base_params.update(params)

        model = RandomForestClassifier(**base_params)
        logger.info(f"RandomForest model built with params: {base_params}")
        return model

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        params: Optional[Dict[str, Any]] = None,
    ) -> RandomForestClassifier:
        """
        Fit the Random Forest on training data.

        Args:
            X_train: Training features
            y_train: Training labels
            params: Optional parameter overrides

        Returns:
            Fitted RandomForestClassifier
        """
        logger.info(f"Training Random Forest | X_train shape: {X_train.shape}")
        self.model = self.build_model(params)
        self._feature_names = X_train.columns.tolist()
        self.model.fit(X_train, y_train)
        oob_score = self._compute_oob_score(X_train, y_train)
        logger.info(f"Random Forest training complete. OOB score: {oob_score:.4f}")
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
            f"RF Cross-Validation ({cv}-fold, {scoring}): "
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

    def _compute_oob_score(
        self, X_train: pd.DataFrame, y_train: pd.Series
    ) -> float:
        """Compute Out-of-Bag score by retraining with oob_score=True."""
        try:
            oob_model = RandomForestClassifier(
                **{
                    **{k: getattr(self.config, k) for k in [
                        "n_estimators", "max_depth", "min_samples_split",
                        "min_samples_leaf", "max_features", "random_state",
                    ]},
                    "oob_score": True,
                    "n_jobs": self.config.n_jobs,
                    "class_weight": self.config.class_weight,
                }
            )
            oob_model.fit(X_train, y_train)
            return oob_model.oob_score_
        except Exception as exc:
            logger.warning(f"OOB score computation failed: {exc}")
            return 0.0