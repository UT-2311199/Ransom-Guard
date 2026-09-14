"""
File: ml/main.py
Main entry point for the RansomGuard ML module.

Run from project root:
  python ml/main.py --mode train
  python ml/main.py --mode train --dataset ml/dataset/data/mlran_dataset.csv
  python ml/main.py --mode predict
"""

import sys
import argparse
import logging
from pathlib import Path

# Ensure project root is on sys.path so `ml.*` imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.training.pipeline import TrainingPipeline
from ml.predictor.predictor import RansomwarePredictor
from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, DatasetConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = get_logger("ml.main")


# ---------------------------------------------------------------------------
# Training mode
# ---------------------------------------------------------------------------

def run_training(
    dataset_path: str = None,
    tune: bool = False,
    tune_method: str = "random",
    tune_n_iter: int = 20,
    cv_folds: int = 5,
) -> dict:
    """
    Run the full training pipeline.

    Steps:
      1. Load dataset (ml/dataset/data/mlran_dataset.csv by default)
      2. Feature engineering & normalization
      3. Train/test split
      4. Train Random Forest + XGBoost
      5. Evaluate & compare models
      6. Save best model + scaler to ml/models/saved/

    Args:
        dataset_path: Optional override path to a CSV dataset file.
        tune: Whether to run hyperparameter tuning.
        tune_method: Tuning strategy ('grid', 'random', 'bayesian').
        tune_n_iter: Iterations for random/bayesian search.
        cv_folds: Cross-validation folds.

    Returns:
        Dictionary of training results and metrics.
    """
    logger.info("=" * 60)
    logger.info("RansomGuard ML — Training Mode")
    logger.info("=" * 60)

    dataset_config = DatasetConfig()
    if dataset_path:
        p = Path(dataset_path)
        dataset_config.dataset_dir = str(p.parent)
        dataset_config.mlran_filename = p.name
        logger.info(f"Using dataset: {dataset_path}")
    else:
        default = Path(dataset_config.dataset_dir) / dataset_config.mlran_filename
        logger.info(f"Using default dataset: {default}")

    pipeline = TrainingPipeline(
        dataset_config=dataset_config,
        tune_hyperparams=tune,
        tune_method=tune_method,
        tune_n_iter=tune_n_iter,
        cv_folds=cv_folds,
    )

    results = pipeline.run()
    logger.info("Training complete.")
    return results


# ---------------------------------------------------------------------------
# Inference mode
# ---------------------------------------------------------------------------

def run_inference(features: dict = None) -> dict:
    """
    Run inference using the saved best model.

    Args:
        features: Dict of feature name -> value. If None, uses a demo vector.

    Returns:
        Prediction result dict with probability, risk level, etc.
    """
    logger.info("=" * 60)
    logger.info("RansomGuard ML — Inference Mode")
    logger.info("=" * 60)

    predictor = RansomwarePredictor()
    predictor.load()

    if features is None:
        # Demo: benign-like feature vector
        features = {
            "files_modified_per_sec": 0.5,
            "files_created": 2,
            "files_deleted": 1,
            "rename_operations": 0,
            "read_operations": 50,
            "write_operations": 5,
            "entropy": 4.2,
            "cpu_usage": 15.0,
            "memory_usage": 30.0,
            "disk_io": 1024,
            "extension_changes": 0,
            "directories_accessed": 3,
            "encryption_ratio": 0.01,
        }
        logger.info("No features provided — using demo benign-like vector.")

    result = predictor.predict(features)

    print("\n--- Prediction Result ---")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print("-------------------------\n")

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="RansomGuard ML Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train using default dataset (ml/dataset/data/mlran_dataset.csv):
  python ml/main.py --mode train

  # Train with a custom dataset path:
  python ml/main.py --mode train --dataset path/to/data.csv

  # Train with hyperparameter tuning:
  python ml/main.py --mode train --tune --tune-method random --tune-n-iter 20

  # Run inference demo with saved model:
  python ml/main.py --mode predict
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["train", "predict"],
        default="train",
        help="Pipeline mode: train or predict (default: train)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to CSV dataset file (overrides config default)",
    )
    parser.add_argument(
        "--tune",
        action="store_true",
        help="Enable hyperparameter tuning during training",
    )
    parser.add_argument(
        "--tune-method",
        choices=["grid", "random", "bayesian"],
        default="random",
        dest="tune_method",
        help="Hyperparameter tuning method (default: random)",
    )
    parser.add_argument(
        "--tune-n-iter",
        type=int,
        default=20,
        dest="tune_n_iter",
        help="Iterations for random/bayesian tuning (default: 20)",
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        dest="cv_folds",
        help="Cross-validation folds (default: 5)",
    )

    args = parser.parse_args()

    if args.mode == "train":
        run_training(
            dataset_path=args.dataset,
            tune=args.tune,
            tune_method=args.tune_method,
            tune_n_iter=args.tune_n_iter,
            cv_folds=args.cv_folds,
        )
    elif args.mode == "predict":
        run_inference()


if __name__ == "__main__":
    main()