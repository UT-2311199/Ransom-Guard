# ml/training/pipeline.py

import os
import json
import time
from typing import Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ml.dataset.loader import DatasetLoader
from ml.feature_extractor.engineer import FeatureEngineer
from ml.training.random_forest_trainer import RandomForestTrainer
from ml.training.xgboost_trainer import XGBoostTrainer
from ml.training.hyperparameter_tuner import HyperparameterTuner
from ml.evaluation.evaluator import ModelEvaluator
from ml.models.model_registry import ModelRegistry
from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, DatasetConfig, ModelConfig

logger = get_logger(__name__)


class TrainingPipeline:
    """
    End-to-end training pipeline:
    Load -> Clean -> Engineer -> Split -> Train RF & XGB ->
    Compare -> Tune -> Evaluate -> Save
    """

    def __init__(
        self,
        dataset_config: Optional[DatasetConfig] = None,
        model_config: Optional[ModelConfig] = None,
        tune_hyperparams: bool = False,
        tune_method: str = "random",
        tune_n_iter: int = 20,
        cv_folds: int = 5,
    ):
        self.dataset_config = dataset_config or CONFIG.dataset
        self.model_config = model_config or CONFIG.model
        self.tune_hyperparams = tune_hyperparams
        self.tune_method = tune_method
        self.tune_n_iter = tune_n_iter
        self.cv_folds = cv_folds

        self.loader = DatasetLoader(dataset_config=self.dataset_config)
        self.engineer = FeatureEngineer()
        self.rf_trainer = RandomForestTrainer()
        self.xgb_trainer = XGBoostTrainer()
        self.tuner = HyperparameterTuner()
        self.evaluator = ModelEvaluator()
        self.registry = ModelRegistry(model_config=self.model_config)

        self.results: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Main Pipeline
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Execute the full training pipeline.

        Returns:
            Dictionary of results (metrics, model paths, comparison)
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("RansomGuard Training Pipeline Starting")
        logger.info("=" * 60)

        # 1. Load Dataset
        logger.info("[1/9] Loading dataset...")
        df = self.loader.load()
        dataset_stats = self.loader.get_dataset_stats(df)
        logger.info(f"Dataset stats: {dataset_stats['total_samples']} samples")

        # 2. Feature/Label Split
        logger.info("[2/9] Splitting features and labels...")
        X, y = self.loader.get_feature_label_split(df)
        logger.info(f"Feature matrix: {X.shape} | Labels: {y.shape}")

        # 3. Feature Engineering & Normalization
        logger.info("[3/9] Applying feature engineering and normalization...")
        X_transformed = self.engineer.fit_transform(X)
        feature_names = X_transformed.columns.tolist()
        logger.info(f"Engineered features: {len(feature_names)}")

        # 4. Train/Test Split
        logger.info("[4/9] Splitting train/test sets...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_transformed,
            y,
            test_size=self.dataset_config.test_size,
            random_state=self.dataset_config.random_state,
            stratify=y if self.dataset_config.stratify else None,
        )
        logger.info(
            f"Train: {X_train.shape[0]} samples | Test: {X_test.shape[0]} samples"
        )

        # 5. Train Random Forest
        logger.info("[5/9] Training Random Forest...")
        rf_params = None
        if self.tune_hyperparams:
            logger.info("  -> Tuning Random Forest hyperparameters...")
            tune_result = self.tuner.tune_random_forest(
                X_train, y_train,
                method=self.tune_method,
                n_iter=self.tune_n_iter,
                cv=self.cv_folds,
            )
            rf_params = tune_result["best_params"]

        rf_model = self.rf_trainer.train(X_train, y_train, params=rf_params)

        # 6. Train XGBoost
        logger.info("[6/9] Training XGBoost...")
        xgb_params = None
        if self.tune_hyperparams:
            logger.info("  -> Tuning XGBoost hyperparameters...")
            tune_result = self.tuner.tune_xgboost(
                X_train, y_train,
                method=self.tune_method,
                n_iter=self.tune_n_iter,
                cv=self.cv_folds,
            )
            xgb_params = tune_result["best_params"]

        # Split validation set from training for XGBoost early stopping
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train, y_train, test_size=0.1, random_state=42, stratify=y_train
        )
        xgb_model = self.xgb_trainer.train(
            X_tr, y_tr, X_val=X_val, y_val=y_val, params=xgb_params
        )

        # 7. Evaluate Both Models
        logger.info("[7/9] Evaluating models...")
        rf_metrics = self.evaluator.evaluate(
            rf_model, X_test, y_test, model_name="RandomForest"
        )
        xgb_metrics = self.evaluator.evaluate(
            xgb_model, X_test, y_test, model_name="XGBoost"
        )

        # 8. Compare Models
        logger.info("[8/9] Comparing models...")
        comparison = self._compare_models(rf_metrics, xgb_metrics)
        best_model_name = comparison["best_model"]
        best_model = rf_model if best_model_name == "RandomForest" else xgb_model
        best_trainer = self.rf_trainer if best_model_name == "RandomForest" else self.xgb_trainer
        logger.info(f"Best model: {best_model_name}")

        # 9. Save Models
        logger.info("[9/9] Saving models...")
        saved_paths = self.registry.save_all(
            rf_model=rf_model,
            xgb_model=xgb_model,
            best_model=best_model,
            best_model_name=best_model_name,
            scaler=self.engineer.scaler,
            feature_names=feature_names,
            rf_metrics=rf_metrics,
            xgb_metrics=xgb_metrics,
            dataset_stats=dataset_stats,
        )

        elapsed = time.time() - start_time
        logger.info(f"Pipeline complete in {elapsed:.1f}s")
        logger.info("=" * 60)

        self.results = {
            "dataset_stats": dataset_stats,
            "feature_names": feature_names,
            "rf_metrics": rf_metrics,
            "xgb_metrics": xgb_metrics,
            "comparison": comparison,
            "best_model_name": best_model_name,
            "saved_paths": saved_paths,
            "elapsed_seconds": elapsed,
        }

        self._print_summary()
        return self.results

    # ------------------------------------------------------------------
    # Private Methods
    # ------------------------------------------------------------------

    def _compare_models(
        self, rf_metrics: Dict[str, Any], xgb_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare RF and XGB on multiple metrics and pick the best model.
        Uses weighted scoring across F1, ROC-AUC, Precision, Recall.
        """
        weights = {
            "f1": 0.40,
            "roc_auc": 0.30,
            "precision": 0.15,
            "recall": 0.15,
        }

        rf_score = sum(
            rf_metrics.get(metric, 0) * weight
            for metric, weight in weights.items()
        )
        xgb_score = sum(
            xgb_metrics.get(metric, 0) * weight
            for metric, weight in weights.items()
        )

        best_model = "RandomForest" if rf_score >= xgb_score else "XGBoost"

        comparison = {
            "RandomForest": {
                "composite_score": round(rf_score, 4),
                "metrics": {k: rf_metrics.get(k) for k in weights},
            },
            "XGBoost": {
                "composite_score": round(xgb_score, 4),
                "metrics": {k: xgb_metrics.get(k) for k in weights},
            },
            "best_model": best_model,
            "margin": round(abs(rf_score - xgb_score), 4),
        }

        logger.info(f"RF composite score: {rf_score:.4f}")
        logger.info(f"XGB composite score: {xgb_score:.4f}")
        logger.info(f"Winner: {best_model} (margin: {comparison['margin']:.4f})")
        return comparison

    def _print_summary(self) -> None:
        """Print a formatted summary of training results."""
        r = self.results
        print("\n" + "=" * 60)
        print("  RANSOMGUARD TRAINING SUMMARY")
        print("=" * 60)
        print(f"  Dataset samples  : {r['dataset_stats']['total_samples']}")
        print(f"  Feature count    : {len(r['feature_names'])}")
        print(f"  Elapsed          : {r['elapsed_seconds']:.1f}s")
        print(f"\n  {'Model':<20} {'Accuracy':<12} {'F1':<12} {'ROC-AUC':<12}")
        print(f"  {'-'*56}")
        for name, metrics in [
            ("RandomForest", r["rf_metrics"]),
            ("XGBoost", r["xgb_metrics"]),
        ]:
            marker = " <-- BEST" if name == r["best_model_name"] else ""
            print(
                f"  {name:<20} "
                f"{metrics.get('accuracy', 0):<12.4f} "
                f"{metrics.get('f1', 0):<12.4f} "
                f"{metrics.get('roc_auc', 0):<12.4f}"
                f"{marker}"
            )
        print("=" * 60)