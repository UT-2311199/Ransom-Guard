# ml/utils/config.py

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class DatasetConfig:
    dataset_dir: str = os.path.join(BASE_DIR, "dataset", "data")
    mlran_filename: str = "mlran_dataset.csv"
    custom_datasets: List[str] = field(default_factory=list)
    test_size: float = 0.2
    random_state: int = 42
    label_column: str = "label"
    stratify: bool = True


@dataclass
class FeatureConfig:
    feature_columns: List[str] = field(
        default_factory=lambda: [
            "files_modified_per_sec",
            "files_created",
            "files_deleted",
            "rename_operations",
            "read_operations",
            "write_operations",
            "entropy",
            "cpu_usage",
            "memory_usage",
            "disk_io",
            "extension_changes",
            "directories_accessed",
            "encryption_ratio",
        ]
    )
    categorical_columns: List[str] = field(default_factory=list)
    scaling_method: str = "standard"  # 'standard', 'minmax', 'robust'
    entropy_threshold: float = 7.0
    encryption_ratio_threshold: float = 0.6


@dataclass
class ModelConfig:
    model_dir: str = os.path.join(BASE_DIR, "models", "saved")
    best_model_filename: str = "best_model.joblib"
    rf_model_filename: str = "random_forest.joblib"
    xgb_model_filename: str = "xgboost.joblib"
    scaler_filename: str = "scaler.joblib"
    metadata_filename: str = "model_metadata.json"


@dataclass
class RandomForestConfig:
    n_estimators: int = 200
    max_depth: Optional[int] = None
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    max_features: str = "sqrt"
    class_weight: str = "balanced"
    random_state: int = 42
    n_jobs: int = -1

    # Hyperparameter search space
    param_grid: Dict[str, Any] = field(
        default_factory=lambda: {
            "n_estimators": [100, 200, 300],
            "max_depth": [None, 10, 20, 30],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
            "max_features": ["sqrt", "log2"],
        }
    )


@dataclass
class XGBoostConfig:
    n_estimators: int = 200
    max_depth: int = 6
    learning_rate: float = 0.1
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    use_label_encoder: bool = False
    eval_metric: str = "logloss"
    random_state: int = 42
    n_jobs: int = -1
    scale_pos_weight: float = 1.0

    # Hyperparameter search space
    param_grid: Dict[str, Any] = field(
        default_factory=lambda: {
            "n_estimators": [100, 200, 300],
            "max_depth": [4, 6, 8],
            "learning_rate": [0.01, 0.1, 0.2],
            "subsample": [0.7, 0.8, 0.9],
            "colsample_bytree": [0.7, 0.8, 0.9],
        }
    )


@dataclass
class MonitoringConfig:
    watch_directory: str = os.path.expanduser("~")
    collection_interval: float = 5.0  # seconds
    feature_window: float = 10.0  # seconds for rolling window
    process_poll_interval: float = 1.0
    alert_threshold: float = 0.75
    high_risk_threshold: float = 0.90
    auto_kill_enabled: bool = False
    quarantine_enabled: bool = True
    quarantine_dir: str = os.path.join(BASE_DIR, "quarantine")
    backup_dir: str = os.path.join(BASE_DIR, "backups")
    timeline_max_events: int = 10000


@dataclass
class RiskConfig:
    low_risk_max: float = 0.30
    medium_risk_max: float = 0.60
    high_risk_max: float = 0.85
    critical_risk_max: float = 1.0
    risk_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "model_probability": 0.50,
            "entropy_score": 0.15,
            "encryption_ratio_score": 0.15,
            "file_activity_score": 0.10,
            "process_score": 0.10,
        }
    )


@dataclass
class Config:
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    random_forest: RandomForestConfig = field(default_factory=RandomForestConfig)
    xgboost: XGBoostConfig = field(default_factory=XGBoostConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)


# Global configuration instance
CONFIG = Config()