"""Generate a synthetic MLRan-format dataset for development/testing."""
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)
n_benign = 2000
n_ransom = 2000


def make_benign(n):
    return pd.DataFrame({
        "files_modified_per_sec": np.random.exponential(0.3, n),
        "files_created":          np.random.poisson(2, n).astype(float),
        "files_deleted":          np.random.poisson(1, n).astype(float),
        "rename_operations":      np.random.poisson(0.5, n).astype(float),
        "read_operations":        np.random.poisson(50, n).astype(float),
        "write_operations":       np.random.poisson(5, n).astype(float),
        "entropy":                np.random.normal(4.5, 1.0, n).clip(0, 8),
        "cpu_usage":              np.random.normal(20, 10, n).clip(0, 100),
        "memory_usage":           np.random.normal(35, 15, n).clip(0, 100),
        "disk_io":                np.random.exponential(2000, n),
        "extension_changes":      np.random.poisson(0.1, n).astype(float),
        "directories_accessed":   np.random.poisson(5, n).astype(float),
        "encryption_ratio":       np.random.beta(1, 20, n),
        "label":                  0,
    })


def make_ransomware(n):
    return pd.DataFrame({
        "files_modified_per_sec": np.random.exponential(8, n),
        "files_created":          np.random.poisson(30, n).astype(float),
        "files_deleted":          np.random.poisson(25, n).astype(float),
        "rename_operations":      np.random.poisson(20, n).astype(float),
        "read_operations":        np.random.poisson(200, n).astype(float),
        "write_operations":       np.random.poisson(180, n).astype(float),
        "entropy":                np.random.normal(7.2, 0.5, n).clip(0, 8),
        "cpu_usage":              np.random.normal(75, 15, n).clip(0, 100),
        "memory_usage":           np.random.normal(70, 10, n).clip(0, 100),
        "disk_io":                np.random.exponential(50000, n),
        "extension_changes":      np.random.poisson(15, n).astype(float),
        "directories_accessed":   np.random.poisson(50, n).astype(float),
        "encryption_ratio":       np.random.beta(8, 2, n),
        "label":                  1,
    })


if __name__ == "__main__":
    df = pd.concat([make_benign(n_benign), make_ransomware(n_ransom)], ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    out = Path(__file__).parent
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / "mlran_dataset.csv"
    df.to_csv(out_path, index=False)

    dist = df["label"].value_counts().to_dict()
    print(f"Dataset created: {len(df)} rows, {df.shape[1]} columns")
    print(f"Label distribution: {dist} (0=benign, 1=ransomware)")
    print(f"Saved to: {out_path}")
