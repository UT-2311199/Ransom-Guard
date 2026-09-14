# ml/dataset/loader.py

import os
import glob
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.utils import resample

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, DatasetConfig, FeatureConfig

logger = get_logger(__name__)


class DatasetLoader:
    """
    Loads, validates, cleans, and merges ransomware detection datasets.
    Supports the MLRan dataset and custom CSV datasets.
    """

    # Expected MLRan column mapping (raw -> normalized)
    MLRAN_COLUMN_MAP: Dict[str, str] = {
        # File system activity
        "filesModifiedPerSec": "files_modified_per_sec",
        "files_modified_per_sec": "files_modified_per_sec",
        "filesCreated": "files_created",
        "files_created": "files_created",
        "filesDeleted": "files_deleted",
        "files_deleted": "files_deleted",
        "renameOps": "rename_operations",
        "rename_operations": "rename_operations",
        "readOps": "read_operations",
        "read_operations": "read_operations",
        "writeOps": "write_operations",
        "write_operations": "write_operations",
        # Entropy
        "entropy": "entropy",
        "fileEntropy": "entropy",
        # System resources
        "cpuUsage": "cpu_usage",
        "cpu_usage": "cpu_usage",
        "memoryUsage": "memory_usage",
        "memory_usage": "memory_usage",
        "diskIO": "disk_io",
        "disk_io": "disk_io",
        # Extension / directory
        "extensionChanges": "extension_changes",
        "extension_changes": "extension_changes",
        "directoriesAccessed": "directories_accessed",
        "directories_accessed": "directories_accessed",
        # Encryption
        "encryptionRatio": "encryption_ratio",
        "encryption_ratio": "encryption_ratio",
        # Labels
        "label": "label",
        "Label": "label",
        "is_ransomware": "label",
        "class": "label",
        "Category": "label",
        "malware": "label",
    }

    LABEL_MAP: Dict[Any, int] = {
        "ransomware": 1,
        "Ransomware": 1,
        "benign": 0,
        "Benign": 0,
        "normal": 0,
        "Normal": 0,
        "malware": 1,
        "Malware": 1,
        1: 1,
        0: 0,
        "1": 1,
        "0": 0,
        True: 1,
        False: 0,
    }

    def __init__(
        self,
        dataset_config: Optional[DatasetConfig] = None,
        feature_config: Optional[FeatureConfig] = None,
    ):
        self.dataset_config = dataset_config or CONFIG.dataset
        self.feature_config = feature_config or CONFIG.features
        self.feature_columns = self.feature_config.feature_columns
        self.label_column = self.dataset_config.label_column
        self._raw_dataframes: List[pd.DataFrame] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> pd.DataFrame:
        """
        Load all configured datasets, merge, clean, and return.

        Returns:
            Cleaned and merged DataFrame
        """
        self._raw_dataframes = []

        # Load MLRan dataset
        mlran_path = os.path.join(
            self.dataset_config.dataset_dir,
            self.dataset_config.mlran_filename,
        )
        if os.path.exists(mlran_path):
            df = self._load_single_file(mlran_path, dataset_name="MLRan")
            if df is not None:
                self._raw_dataframes.append(df)
        else:
            logger.warning(f"MLRan dataset not found at: {mlran_path}")

        # Load custom datasets
        for custom_path in self.dataset_config.custom_datasets:
            if os.path.exists(custom_path):
                df = self._load_single_file(custom_path, dataset_name=os.path.basename(custom_path))
                if df is not None:
                    self._raw_dataframes.append(df)
            else:
                logger.warning(f"Custom dataset not found: {custom_path}")

        # Auto-discover datasets in the dataset directory
        if not self._raw_dataframes:
            logger.info("No explicit datasets found. Scanning dataset directory...")
            self._raw_dataframes = self._discover_datasets()

        if not self._raw_dataframes:
            logger.warning("No datasets loaded. Generating synthetic dataset for testing.")
            return self._generate_synthetic_dataset()

        merged = self._merge_dataframes(self._raw_dataframes)
        cleaned = self._clean_dataframe(merged)
        logger.info(
            f"Final dataset: {len(cleaned)} rows | "
            f"Ransomware: {cleaned[self.label_column].sum()} | "
            f"Benign: {(cleaned[self.label_column] == 0).sum()}"
        )
        return cleaned

    def add_custom_dataset(self, file_path: str) -> None:
        """
        Register an additional CSV dataset file path.

        Args:
            file_path: Absolute or relative path to CSV file
        """
        abs_path = os.path.abspath(file_path)
        if abs_path not in self.dataset_config.custom_datasets:
            self.dataset_config.custom_datasets.append(abs_path)
            logger.info(f"Custom dataset registered: {abs_path}")

    def get_feature_label_split(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Split DataFrame into features (X) and labels (y).

        Args:
            df: Cleaned DataFrame

        Returns:
            Tuple of (X, y)
        """
        available_features = [c for c in self.feature_columns if c in df.columns]
        missing = [c for c in self.feature_columns if c not in df.columns]
        if missing:
            logger.warning(f"Missing feature columns (will be skipped): {missing}")

        X = df[available_features].copy()
        y = df[self.label_column].copy()
        return X, y

    def get_dataset_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return descriptive statistics about the loaded dataset."""
        stats = {
            "total_samples": len(df),
            "ransomware_samples": int(df[self.label_column].sum()),
            "benign_samples": int((df[self.label_column] == 0).sum()),
            "class_balance": float(df[self.label_column].mean()),
            "feature_count": len([c for c in self.feature_columns if c in df.columns]),
            "null_counts": df.isnull().sum().to_dict(),
            "feature_stats": df[
                [c for c in self.feature_columns if c in df.columns]
            ].describe().to_dict(),
        }
        return stats

    # ------------------------------------------------------------------
    # Private Methods
    # ------------------------------------------------------------------

    def _load_single_file(
        self, path: str, dataset_name: str = "Unknown"
    ) -> Optional[pd.DataFrame]:
        """Load and normalize a single CSV file."""
        try:
            logger.info(f"Loading dataset [{dataset_name}]: {path}")
            df = pd.read_csv(path, low_memory=False)
            logger.info(f"  Raw shape: {df.shape}")
            df = self._normalize_columns(df)
            df = self._normalize_labels(df)
            logger.info(f"  Normalized shape: {df.shape}")
            return df
        except Exception as exc:
            logger.error(f"Failed to load dataset [{dataset_name}]: {exc}")
            return None

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns to standardized names."""
        rename_map = {}
        for col in df.columns:
            if col in self.MLRAN_COLUMN_MAP:
                rename_map[col] = self.MLRAN_COLUMN_MAP[col]
        if rename_map:
            df = df.rename(columns=rename_map)
            logger.debug(f"  Renamed columns: {rename_map}")
        return df

    def _normalize_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize label column to binary integer (0/1)."""
        if self.label_column not in df.columns:
            logger.error(f"Label column '{self.label_column}' not found in dataset.")
            logger.error(f"Available columns: {list(df.columns)}")
            raise ValueError(f"Label column '{self.label_column}' not found.")

        df[self.label_column] = df[self.label_column].map(self.LABEL_MAP)

        unmapped = df[self.label_column].isnull().sum()
        if unmapped > 0:
            logger.warning(f"  {unmapped} labels could not be mapped and will be dropped.")
            df = df.dropna(subset=[self.label_column])

        df[self.label_column] = df[self.label_column].astype(int)
        return df

    def _merge_dataframes(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """Concatenate multiple DataFrames into one."""
        if len(dataframes) == 1:
            return dataframes[0]

        logger.info(f"Merging {len(dataframes)} datasets...")
        merged = pd.concat(dataframes, axis=0, ignore_index=True)
        logger.info(f"Merged shape: {merged.shape}")
        return merged

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform data cleaning:
        - Drop duplicates
        - Handle missing values
        - Remove outliers
        - Ensure correct dtypes
        - Balance classes if needed
        """
        initial_len = len(df)

        # Keep only relevant columns
        keep_cols = [c for c in self.feature_columns if c in df.columns] + [self.label_column]
        df = df[keep_cols].copy()

        # Drop exact duplicates
        df.drop_duplicates(inplace=True)
        logger.info(f"  After dedup: {len(df)} rows (removed {initial_len - len(df)})")

        # Numeric coercion
        for col in [c for c in self.feature_columns if c in df.columns]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Fill missing values with column median
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if self.label_column in numeric_cols:
            numeric_cols.remove(self.label_column)

        for col in numeric_cols:
            if df[col].isnull().any():
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                logger.debug(f"  Filled '{col}' NaNs with median={median_val:.4f}")

        # Drop rows with NaN in label
        before = len(df)
        df = df.dropna(subset=[self.label_column])
        if len(df) < before:
            logger.warning(f"  Dropped {before - len(df)} rows with NaN labels.")

        # Clip extreme outliers (IQR-based, per feature column)
        df = self._clip_outliers(df)

        # Reset index
        df.reset_index(drop=True, inplace=True)

        logger.info(f"  Final clean shape: {df.shape}")
        return df

    def _clip_outliers(self, df: pd.DataFrame, multiplier: float = 5.0) -> pd.DataFrame:
        """
        Clip values beyond median ± multiplier * IQR for each feature column.
        Uses a conservative multiplier to preserve ransomware-specific spikes.
        """
        for col in [c for c in self.feature_columns if c in df.columns]:
            Q1 = df[col].quantile(0.01)
            Q3 = df[col].quantile(0.99)
            IQR = Q3 - Q1
            lower = Q1 - multiplier * IQR
            upper = Q3 + multiplier * IQR
            clipped = df[col].clip(lower=lower, upper=upper)
            if not clipped.equals(df[col]):
                logger.debug(f"  Clipped outliers in '{col}': [{lower:.2f}, {upper:.2f}]")
            df[col] = clipped
        return df

    def _discover_datasets(self) -> List[pd.DataFrame]:
        """Auto-discover CSV files in the dataset directory."""
        pattern = os.path.join(self.dataset_config.dataset_dir, "**", "*.csv")
        csv_files = glob.glob(pattern, recursive=True)
        dataframes = []
        for f in csv_files:
            df = self._load_single_file(f, dataset_name=os.path.basename(f))
            if df is not None:
                dataframes.append(df)
        return dataframes

    def _generate_synthetic_dataset(self, n_samples: int = 5000) -> pd.DataFrame:
        """
        Generate a synthetic ransomware dataset for testing purposes.
        Feature distributions are based on typical ransomware vs. benign behavior.
        """
        logger.warning("Generating synthetic dataset — NOT for production use.")
        np.random.seed(42)

        half = n_samples // 2

        # Benign samples
        benign = pd.DataFrame({
            "files_modified_per_sec": np.random.normal(2, 1, half).clip(0),
            "files_created": np.random.normal(5, 3, half).clip(0),
            "files_deleted": np.random.normal(2, 1, half).clip(0),
            "rename_operations": np.random.normal(1, 0.5, half).clip(0),
            "read_operations": np.random.normal(100, 50, half).clip(0),
            "write_operations": np.random.normal(20, 10, half).clip(0),
            "entropy": np.random.normal(4.5, 0.8, half).clip(0, 8),
            "cpu_usage": np.random.normal(25, 15, half).clip(0, 100),
            "memory_usage": np.random.normal(40, 10, half).clip(0, 100),
            "disk_io": np.random.normal(10, 5, half).clip(0),
            "extension_changes": np.random.poisson(0.1, half),
            "directories_accessed": np.random.normal(10, 5, half).clip(0),
            "encryption_ratio": np.random.normal(0.05, 0.05, half).clip(0, 1),
            "label": 0,
        })

        # Ransomware samples
        ransomware = pd.DataFrame({
            "files_modified_per_sec": np.random.normal(120, 40, half).clip(0),
            "files_created": np.random.normal(200, 80, half).clip(0),
            "files_deleted": np.random.normal(150, 60, half).clip(0),
            "rename_operations": np.random.normal(180, 50, half).clip(0),
            "read_operations": np.random.normal(800, 200, half).clip(0),
            "write_operations": np.random.normal(600, 150, half).clip(0),
            "entropy": np.random.normal(7.5, 0.3, half).clip(0, 8),
            "cpu_usage": np.random.normal(85, 10, half).clip(0, 100),
            "memory_usage": np.random.normal(75, 10, half).clip(0, 100),
            "disk_io": np.random.normal(200, 50, half).clip(0),
            "extension_changes": np.random.poisson(50, half),
            "directories_accessed": np.random.normal(300, 80, half).clip(0),
            "encryption_ratio": np.random.normal(0.85, 0.1, half).clip(0, 1),
            "label": 1,
        })

        df = pd.concat([benign, ransomware], ignore_index=True)
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        logger.info(f"Synthetic dataset created: {df.shape}")
        return df