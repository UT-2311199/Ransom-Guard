import os
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import setup_logger
from utils.helpers import (
    calculate_file_entropy,
    is_suspicious_extension,
    detect_suspicious_keywords,
    get_file_size,
    calculate_risk_score,
    generate_id,
)

logger = setup_logger("ml_model", "logs/prediction.log")


# Ransomware-associated file extensions
RANSOMWARE_EXTENSIONS = {
    "encrypted", "enc", "crypt", "crypted", "crypto", "locked",
    "lock", "locker", "ransom", "wcry", "wncry", "wncryt",
    "cerber", "cerber2", "zepto", "locky", "thor", "odin",
    "r5a", "r4a", "pays", "pays2", "ecc", "ezz", "exx",
    "xyz", "zzz", "xxx", "micro", "cryptolocker", "darkness",
}

# High-risk file extensions targeted by ransomware
HIGH_VALUE_EXTENSIONS = {
    "doc", "docx", "xls", "xlsx", "ppt", "pptx", "pdf",
    "jpg", "jpeg", "png", "bmp", "gif", "tiff", "raw",
    "mp4", "avi", "mov", "mkv", "mp3", "wav", "flac",
    "zip", "rar", "7z", "tar", "gz",
    "sql", "db", "sqlite", "mdb", "accdb",
    "psd", "ai", "eps", "cdr",
    "py", "java", "js", "cs", "cpp", "h",
    "txt", "csv", "json", "xml",
    "key", "pem", "cer", "pfx",
}

# Suspicious ransom note filenames
RANSOM_NOTE_NAMES = {
    "readme.txt", "read_me.txt", "how_to_decrypt.txt",
    "decrypt_instructions.txt", "your_files.txt",
    "ransom_note.txt", "recovery.txt", "restore_files.txt",
    "helpdesk.txt", "help.txt",
    "!!readme!!.txt", "!!!read_me!!!.txt",
}


class RansomwareDetector:
    """
    Machine Learning model for ransomware detection.
    Uses a combination of rule-based analysis and trained ML model.
    Falls back to rule-based if model not available.
    """

    MODEL_PATH = "models/ransomware_detector.joblib"
    MODEL_VERSION = "1.0.0"

    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_loaded = False
        self._load_model()

    def _load_model(self):
        """
        Attempt to initialise the ML bridge (RansomwarePredictor).
        Falls back to rule-based if model not trained or ML module unavailable.
        """
        try:
            from services.ml_bridge import get_ml_predictor, is_ml_available
            if is_ml_available():
                self.model_loaded = True
                logger.info("RansomwareDetector: ML bridge ready (using trained model).")
            else:
                logger.warning(
                    "RansomwareDetector: ML bridge unavailable. "
                    "Using rule-based detection fallback."
                )
        except Exception as e:
            logger.error(f"RansomwareDetector: bridge init error: {e}. Using rule-based fallback.")
            self.model_loaded = False

    def extract_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract numerical features from input data for ML prediction.

        Args:
            data: Input data dictionary

        Returns:
            Feature dictionary
        """
        file_path = data.get("file_path", "")
        file_name = data.get("file_name", "").lower()
        file_extension = (data.get("file_extension") or "").lower().lstrip(".")
        file_size = data.get("file_size", 0) or get_file_size(file_path)
        process_name = (data.get("process_name") or "").lower()
        event_type = (data.get("event_type") or "").lower()
        rapid_changes = data.get("rapid_changes", 0)
        extensions_modified = data.get("extensions_modified", [])

        # Calculate entropy
        entropy = data.get("entropy")
        if entropy is None:
            entropy = calculate_file_entropy(file_path)

        # Feature 1: File entropy (0-8)
        f_entropy = float(entropy)

        # Feature 2: Is ransomware extension (0 or 1)
        f_ransomware_ext = 1.0 if file_extension in RANSOMWARE_EXTENSIONS else 0.0

        # Feature 3: Is high-value target extension (0 or 1)
        f_high_value_ext = 1.0 if file_extension in HIGH_VALUE_EXTENSIONS else 0.0

        # Feature 4: Is ransom note filename (0 or 1)
        f_ransom_note = 1.0 if file_name in RANSOM_NOTE_NAMES else 0.0

        # Feature 5: Number of extensions modified
        f_ext_variety = float(min(len(set(extensions_modified)), 50))

        # Feature 6: Rapid file changes
        f_rapid_changes = float(min(rapid_changes, 1000))

        # Feature 7: Event type encoding
        event_scores = {
            "created": 0.3,
            "modified": 0.5,
            "deleted": 0.4,
            "renamed": 0.7,
            "moved": 0.6,
        }
        f_event_type = event_scores.get(event_type, 0.0)

        # Feature 8: File size (normalized, log scale)
        f_file_size = np.log1p(file_size) if file_size > 0 else 0.0

        # Feature 9: Suspicious keywords in file
        suspicious_keywords = data.get("suspicious_keywords", [])
        if not suspicious_keywords and os.path.exists(file_path):
            suspicious_keywords = detect_suspicious_keywords(file_path)
        f_keywords = float(min(len(suspicious_keywords), 10))

        # Feature 10: Process suspicion
        suspicious_proc_patterns = {
            "cmd", "powershell", "wscript", "cscript",
            "rundll32", "regsvr32", "mshta", "wmic",
        }
        f_suspicious_proc = 1.0 if any(
            p in process_name for p in suspicious_proc_patterns
        ) else 0.0

        features = {
            "entropy": f_entropy,
            "ransomware_extension": f_ransomware_ext,
            "high_value_extension": f_high_value_ext,
            "ransom_note": f_ransom_note,
            "extension_variety": f_ext_variety,
            "rapid_changes": f_rapid_changes,
            "event_type_score": f_event_type,
            "file_size_log": float(f_file_size),
            "suspicious_keywords": f_keywords,
            "suspicious_process": f_suspicious_proc,
        }

        return features

    def _rule_based_predict(
        self, features: Dict[str, float], data: Dict[str, Any]
    ) -> Tuple[bool, float, str, List[str]]:
        """
        Rule-based ransomware detection fallback.

        Args:
            features: Extracted features
            data: Original input data

        Returns:
            Tuple of (is_ransomware, confidence, threat_level, indicators)
        """
        score = 0.0
        indicators = []

        # High entropy (strongly suggests encryption)
        if features["entropy"] > 7.5:
            score += 35
            indicators.append(f"Very high file entropy: {features['entropy']:.2f} (suggests encryption)")
        elif features["entropy"] > 7.0:
            score += 20
            indicators.append(f"High file entropy: {features['entropy']:.2f}")
        elif features["entropy"] > 6.5:
            score += 10
            indicators.append(f"Elevated file entropy: {features['entropy']:.2f}")

        # Ransomware extension
        if features["ransomware_extension"] == 1.0:
            score += 40
            ext = data.get("file_extension", "")
            indicators.append(f"Known ransomware file extension: .{ext}")

        # Ransom note
        if features["ransom_note"] == 1.0:
            score += 35
            indicators.append(f"Ransom note filename detected: {data.get('file_name', '')}")

        # Extension variety (many different extensions being modified)
        if features["extension_variety"] > 10:
            score += 20
            indicators.append(f"Modifying {int(features['extension_variety'])} different file extensions")
        elif features["extension_variety"] > 5:
            score += 10

        # Rapid file changes
        if features["rapid_changes"] > 100:
            score += 20
            indicators.append(f"Rapid file modifications: {int(features['rapid_changes'])} changes")
        elif features["rapid_changes"] > 50:
            score += 10
            indicators.append(f"Elevated file modification rate: {int(features['rapid_changes'])} changes")

        # Suspicious keywords
        if features["suspicious_keywords"] > 3:
            score += 25
            indicators.append("Multiple ransomware-related keywords found in file")
        elif features["suspicious_keywords"] > 0:
            score += 10
            indicators.append("Ransomware-related keywords found in file")

        # Suspicious process
        if features["suspicious_process"] == 1.0:
            score += 15
            indicators.append(f"Suspicious process: {data.get('process_name', '')}")

        # High-value file being renamed
        if features["high_value_extension"] == 1.0 and features["event_type_score"] >= 0.6:
            score += 15
            indicators.append(f"High-value file being renamed/moved")

        # Normalize to confidence (0-1)
        confidence = min(score / 100.0, 1.0)
        is_ransomware = score >= 45

        # Determine threat level
        if score >= 80:
            threat_level = "critical"
        elif score >= 60:
            threat_level = "high"
        elif score >= 40:
            threat_level = "medium"
        elif score >= 20:
            threat_level = "low"
        else:
            threat_level = "safe"

        return is_ransomware, confidence, threat_level, indicators

    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform ransomware prediction on the given data.

        Strategy:
          1. Try ML bridge (trained RansomwarePredictor) — rich result.
          2. Fall back to rule-based if ML is unavailable.

        Args:
            data: File/event data dictionary

        Returns:
            Prediction result dictionary
        """
        try:
            # ── Try ML bridge first ───────────────────────────────────────
            if self.model_loaded:
                try:
                    from services.ml_bridge import predict_with_ml
                    ml_result = predict_with_ml(data)
                    if ml_result is not None:
                        logger.info(
                            f"ML prediction | File: {data.get('file_name', 'unknown')} | "
                            f"Level: {ml_result['threat_level']} | "
                            f"Ransomware: {ml_result['is_ransomware']}"
                        )
                        return ml_result
                except Exception as e:
                    logger.warning(f"ML bridge predict failed, falling back to rule-based: {e}")

            # ── Rule-based fallback ───────────────────────────────────────
            features = self.extract_features(data)

            is_ransomware = False
            confidence = 0.0
            threat_level = "safe"
            indicators = []

            is_ransomware, confidence, threat_level, indicators = self._rule_based_predict(
                features, data
            )
            logger.debug(f"Rule-based prediction: ransomware={is_ransomware}, confidence={confidence:.3f}")

            # Calculate risk score
            risk_score = calculate_risk_score(
                confidence=confidence,
                is_ransomware=is_ransomware,
                threat_level=threat_level,
                entropy=features.get("entropy", 0.0),
                suspicious_extensions=features.get("ransomware_extension", 0.0) == 1.0,
                rapid_changes=int(features.get("rapid_changes", 0)),
            )

            # Determine recommended action
            recommended_action = self._get_recommended_action(threat_level, is_ransomware)

            # Prepare result
            result = {
                "prediction_id": generate_id(),
                "file_path": data.get("file_path", ""),
                "file_name": data.get("file_name", "") or os.path.basename(data.get("file_path", "")),
                "threat_level": threat_level,
                "confidence": round(confidence, 4),
                "is_ransomware": is_ransomware,
                "risk_score": risk_score,
                "features_analyzed": features,
                "indicators": indicators,
                "recommended_action": recommended_action,
                "model_version": self.MODEL_VERSION,
                "model_type": "ml" if self.model_loaded else "rule_based",
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Prediction complete | File: {data.get('file_name', 'unknown')} | "
                f"Level: {threat_level} | Ransomware: {is_ransomware} | "
                f"Confidence: {confidence:.3f} | Risk: {risk_score}"
            )

            return result

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise

    def _get_recommended_action(self, threat_level: str, is_ransomware: bool) -> str:
        """Get recommended action based on threat level."""
        if threat_level == "critical" or (is_ransomware and threat_level in ["high", "critical"]):
            return "IMMEDIATELY quarantine file and terminate associated process. Isolate system from network."
        elif threat_level == "high":
            return "Quarantine file immediately. Investigate associated process and network connections."
        elif threat_level == "medium":
            return "Monitor file and associated process closely. Consider quarantine if behavior continues."
        elif threat_level == "low":
            return "Log and monitor. No immediate action required."
        else:
            return "No action required. File appears safe."


# Singleton instance
_detector_instance: Optional[RansomwareDetector] = None


def get_detector() -> RansomwareDetector:
    """Get or create the singleton detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = RansomwareDetector()
    return _detector_instance