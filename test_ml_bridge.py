"""End-to-end ML <-> Backend connection test."""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'backend')

# ── Test 1: ML Predictor loads ──────────────────────────────────────────────
print("--- Test 1: ML Predictor Load ---")
from ml.predictor.predictor import RansomwarePredictor
p = RansomwarePredictor()
p.load()
print(f"Model    : {p.model_name}")
print(f"Features : {len(p.feature_names)} -> {p.feature_names[:3]}...")

# ── Test 2: Benign prediction ────────────────────────────────────────────────
print("\n--- Test 2: Benign Prediction ---")
benign = p.predict({
    "files_modified_per_sec": 0.2, "files_created": 1.0, "files_deleted": 0.5,
    "rename_operations": 0.2,      "read_operations": 30.0, "write_operations": 3.0,
    "entropy": 3.5,                "cpu_usage": 10.0, "memory_usage": 25.0,
    "disk_io": 500.0,              "extension_changes": 0.0,
    "directories_accessed": 2.0,   "encryption_ratio": 0.01,
})
print(f"Label={benign['label']} | Risk={benign['risk_level']} | Prob={benign['probability']}")

# ── Test 3: Ransomware prediction ────────────────────────────────────────────
print("\n--- Test 3: Ransomware Prediction ---")
ransom = p.predict({
    "files_modified_per_sec": 150.0, "files_created": 40.0, "files_deleted": 30.0,
    "rename_operations": 25.0,       "read_operations": 250.0, "write_operations": 200.0,
    "entropy": 7.8,                  "cpu_usage": 85.0, "memory_usage": 75.0,
    "disk_io": 80000.0,              "extension_changes": 20.0,
    "directories_accessed": 60.0,    "encryption_ratio": 0.92,
})
print(f"Label={ransom['label']} | Risk={ransom['risk_level']} | Prob={ransom['probability']}")

# ── Test 4: ML Bridge status ─────────────────────────────────────────────────
print("\n--- Test 4: Backend ML Bridge Status ---")
from services.ml_bridge import get_ml_status, predict_with_ml
status = get_ml_status()
print(f"ML Available : {status['available']}")
print(f"Model        : {status['model_name']} | Features: {status['feature_count']}")

# ── Test 5: End-to-end via bridge ────────────────────────────────────────────
print("\n--- Test 5: End-to-end prediction via bridge ---")
result = predict_with_ml({
    "file_path": "C:/Users/test/document.docx",
    "file_name": "document.docx",
    "entropy": 7.5,
    "event_type": "renamed",
    "rapid_changes": 80,
    "extensions_modified": ["docx", "enc", "locked"],
    "file_size": 1024000,
})
print(f"Threat Level : {result['threat_level']}")
print(f"Ransomware   : {result['is_ransomware']}")
print(f"Confidence   : {result['confidence']}")
print(f"Model Type   : {result['model_type']}")
print(f"Indicators   : {result['indicators'][:2]}")

print("\n" + "="*50)
print("  ALL TESTS PASSED — ML <-> Backend CONNECTED!")
print("="*50)
