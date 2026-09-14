# ml/feature_extractor/engineer.py

from typing import Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, FeatureConfig

logger = get_logger(__name__)


class FeatureEngineer:
    """
    Applies feature engineering, derived feature creation,
    and normalization/scaling to the dataset.
    """

    def __init__(self, feature_config: Optional[FeatureConfig] = None):
        self.config = feature_config or CONFIG.features
        self.scaler = self._init_scaler()
        self._fitted = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit_transform(
        self, X: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Fit scaler on X and transform it.

        Args:
            X: Feature DataFrame (training data)

        Returns:
            Scaled and engineered DataFrame
        """
        X_eng = self._add_derived_features(X.copy())
        cols = X_eng.columns.tolist()
        X_scaled = self.scaler.fit_transform(X_eng)
        self._fitted = True
        logger.info(f"FeatureEngineer fitted. Features: {cols}")
        return pd.DataFrame(X_scaled, columns=cols, index=X_eng.index)

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform X using already-fitted scaler.

        Args:
            X: Feature DataFrame (test/live data)

        Returns:
            Scaled and engineered DataFrame
        """
        if not self._fitted:
            raise RuntimeError("FeatureEngineer must be fitted before transform().")

        X_eng = self._add_derived_features(X.copy())

        # Align columns to fitted scaler columns
        expected_cols = self._get_expected_columns(X_eng)
        X_eng = self._align_columns(X_eng, expected_cols)

        X_scaled = self.scaler.transform(X_eng)
        return pd.DataFrame(X_scaled, columns=X_eng.columns.tolist(), index=X_eng.index)

    def transform_dict(self, feature_dict: dict) -> pd.DataFrame:
        """
        Transform a single feature dictionary (for live prediction).

        Args:
            feature_dict: Dictionary of feature_name -> value

        Returns:
            Scaled DataFrame with one row
        """
        df = pd.DataFrame([feature_dict])
        # Fill missing columns with 0
        for col in self.config.feature_columns:
            if col not in df.columns:
                df[col] = 0.0
        return self.transform(df)

    def get_feature_names(self) -> list:
        """Return the list of feature column names after engineering."""
        # Build a dummy dataframe to determine feature names
        dummy = pd.DataFrame(
            [np.zeros(len(self.config.feature_columns))],
            columns=self.config.feature_columns,
        )
        engineered = self._add_derived_features(dummy)
        return engineered.columns.tolist()

    # ------------------------------------------------------------------
    # Private Methods
    # ------------------------------------------------------------------

    def _init_scaler(self):
        method = self.config.scaling_method
        if method == "minmax":
            return MinMaxScaler()
        elif method == "robust":
            return RobustScaler()
        else:  # default: standard
            return StandardScaler()

    def _add_derived_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived/engineered features from base features.
        These capture complex ransomware behavioral patterns.
        """
        eps = 1e-9  # avoid division by zero

        # Ratio of writes to reads (ransomware writes a lot relative to reads)
        if "write_operations" in X.columns and "read_operations" in X.columns:
            X["write_read_ratio"] = X["write_operations"] / (X["read_operations"] + eps)

        # File churn rate: creates + deletes + renames relative to time window
        if all(c in X.columns for c in ["files_created", "files_deleted", "rename_operations"]):
            X["file_churn_rate"] = (
                X["files_created"] + X["files_deleted"] + X["rename_operations"]
            )

        # Entropy × encryption_ratio: combined encryption signal
        if "entropy" in X.columns and "encryption_ratio" in X.columns:
            X["entropy_encryption_product"] = X["entropy"] * X["encryption_ratio"]

        # CPU × Disk IO: compute-heavy disk activity (typical during encryption)
        if "cpu_usage" in X.columns and "disk_io" in X.columns:
            X["cpu_disk_product"] = (X["cpu_usage"] / 100.0) * X["disk_io"]

        # Files modified per directory accessed
        if "files_modified_per_sec" in X.columns and "directories_accessed" in X.columns:
            X["modification_density"] = X["files_modified_per_sec"] / (
                X["directories_accessed"] + eps
            )

        # Extension change rate (extension_changes / total file ops)
        if "extension_changes" in X.columns and "files_modified_per_sec" in X.columns:
            X["extension_change_rate"] = X["extension_changes"] / (
                X["files_modified_per_sec"] + eps
            )

        # High entropy flag (binary)
        if "entropy" in X.columns:
            X["high_entropy_flag"] = (
                X["entropy"] >= self.config.entropy_threshold
            ).astype(float)

        # High encryption flag (binary)
        if "encryption_ratio" in X.columns:
            X["high_encryption_flag"] = (
                X["encryption_ratio"] >= self.config.encryption_ratio_threshold
            ).astype(float)

        return X

    def _get_expected_columns(self, X_eng: pd.DataFrame) -> list:
        """Get the list of columns that the fitted scaler expects."""
        if hasattr(self.scaler, "feature_names_in_"):
            return list(self.scaler.feature_names_in_)
        return X_eng.columns.tolist()

    def _align_columns(
        self, df: pd.DataFrame, expected_cols: list
    ) -> pd.DataFrame:
        """
        Ensure DataFrame has exactly the expected columns in the right order.
        Missing columns are filled with 0; extra columns are dropped.
        """
        for col in expected_cols:
            if col not in df.columns:
                logger.debug(f"Column '{col}' missing in transform input — filling with 0.")
                df[col] = 0.0
        return df[expected_cols]