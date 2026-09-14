# ml/training/hyperparameter_tuner.py

from typing import Optional, Dict, Any, Union, Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    GridSearchCV,
    RandomizedSearchCV,
    StratifiedKFold,
)

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, RandomForestConfig, XGBoostConfig

logger = get_logger(__name__)


class HyperparameterTuner:
    """
    Performs hyperparameter optimization for Random Forest and XGBoost.
    Supports GridSearch and RandomizedSearch with StratifiedKFold.
    """

    def __init__(
        self,
        rf_config: Optional[RandomForestConfig] = None,
        xgb_config: Optional[XGBoostConfig] = None,
    ):
        self.rf_config = rf_config or CONFIG.random_forest
        self.xgb_config = xgb_config or CONFIG.xgboost

    def tune_random_forest(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        param_grid: Optional[Dict[str, Any]] = None,
        method: str = "random",
        n_iter: int = 30,
        cv: int = 5,
        scoring: str = "f1",
        n_jobs: int = -1,
    ) -> Dict[str, Any]:
        """
        Tune Random Forest hyperparameters.

        Args:
            X_train: Training features
            y_train: Training labels
            param_grid: Parameter search space (uses config default if None)
            method: 'grid' or 'random'
            n_iter: Number of iterations for RandomizedSearchCV
            cv: Number of cross-validation folds
            scoring: Sklearn scoring metric
            n_jobs: Parallel jobs

        Returns:
            Dictionary with best_params, best_score, best_estimator
        """
        logger.info(f"Tuning Random Forest | method={method} | scoring={scoring}")
        param_grid = param_grid or self.rf_config.param_grid

        base_model = RandomForestClassifier(
            class_weight=self.rf_config.class_weight,
            random_state=self.rf_config.random_state,
            n_jobs=self.rf_config.n_jobs,
        )

        searcher = self._build_searcher(
            base_model, param_grid, method, n_iter, cv, scoring, n_jobs
        )

        searcher.fit(X_train, y_train)
        result = self._extract_results(searcher)
        logger.info(f"RF Best Score ({scoring}): {result['best_score']:.4f}")
        logger.info(f"RF Best Params: {result['best_params']}")
        return result

    def tune_xgboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        param_grid: Optional[Dict[str, Any]] = None,
        method: str = "random",
        n_iter: int = 30,
        cv: int = 5,
        scoring: str = "f1",
        n_jobs: int = -1,
    ) -> Dict[str, Any]:
        """
        Tune XGBoost hyperparameters.

        Args:
            X_train: Training features
            y_train: Training labels
            param_grid: Parameter search space (uses config default if None)
            method: 'grid' or 'random'
            n_iter: Number of iterations for RandomizedSearchCV
            cv: Number of cross-validation folds
            scoring: Sklearn scoring metric
            n_jobs: Parallel jobs

        Returns:
            Dictionary with best_params, best_score, best_estimator
        """
        if XGBClassifier is None:
            raise ImportError("XGBoost is required: pip install xgboost")

        logger.info(f"Tuning XGBoost | method={method} | scoring={scoring}")
        param_grid = param_grid or self.xgb_config.param_grid

        base_model = XGBClassifier(
            use_label_encoder=False,
            eval_metric=self.xgb_config.eval_metric,
            random_state=self.xgb_config.random_state,
            n_jobs=self.xgb_config.n_jobs,
        )

        searcher = self._build_searcher(
            base_model, param_grid, method, n_iter, cv, scoring, n_jobs
        )

        searcher.fit(X_train, y_train)
        result = self._extract_results(searcher)
        logger.info(f"XGB Best Score ({scoring}): {result['best_score']:.4f}")
        logger.info(f"XGB Best Params: {result['best_params']}")
        return result

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _build_searcher(
        self,
        model,
        param_grid: Dict[str, Any],
        method: str,
        n_iter: int,
        cv: int,
        scoring: str,
        n_jobs: int,
    ) -> Union[GridSearchCV, RandomizedSearchCV]:
        """Construct GridSearchCV or RandomizedSearchCV."""
        cv_strategy = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)

        if method == "grid":
            return GridSearchCV(
                estimator=model,
                param_grid=param_grid,
                cv=cv_strategy,
                scoring=scoring,
                n_jobs=n_jobs,
                refit=True,
                verbose=1,
                return_train_score=True,
            )
        else:  # random
            return RandomizedSearchCV(
                estimator=model,
                param_distributions=param_grid,
                n_iter=n_iter,
                cv=cv_strategy,
                scoring=scoring,
                n_jobs=n_jobs,
                refit=True,
                verbose=1,
                random_state=42,
                return_train_score=True,
            )

    def _extract_results(
        self, searcher: Union[GridSearchCV, RandomizedSearchCV]
    ) -> Dict[str, Any]:
        """Extract key results from a fitted searcher."""
        return {
            "best_params": searcher.best_params_,
            "best_score": float(searcher.best_score_),
            "best_estimator": searcher.best_estimator_,
            "cv_results": {
                "mean_test_score": searcher.cv_results_["mean_test_score"].tolist(),
                "std_test_score": searcher.cv_results_["std_test_score"].tolist(),
                "params": searcher.cv_results_["params"],
            },
        }