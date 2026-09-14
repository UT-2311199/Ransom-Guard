# ml/advanced/risk_scorer.py

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, RiskConfig

logger = get_logger(__name__)


@dataclass
class RiskSnapshot:
    """Represents a point-in-time risk assessment."""
    timestamp: float
    risk_score: float
    risk_level: str
    probability: float
    prediction: int
    label: str
    features: Dict[str, float] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    mitre_techniques: List[Dict] = field(default_factory=list)


class RiskScorer:
    """
    Maintains a rolling risk assessment window.
    Computes trending, escalation detection, and sustained threat scoring.
    """

    def __init__(
        self,
        risk_config: Optional[RiskConfig] = None,
        history_size: int = 100,
        trend_window: int = 10,
    ):
        self.config = risk_config or CONFIG.risk
        self.history_size = history_size
        self.trend_window = trend_window
        self._history: Deque[RiskSnapshot] = deque(maxlen=history_size)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, prediction_result: Dict[str, Any]) -> RiskSnapshot:
        """
        Record a prediction result and return a RiskSnapshot.

        Args:
            prediction_result: Output from RansomwarePredictor.predict()

        Returns:
            RiskSnapshot instance
        """
        snapshot = RiskSnapshot(
            timestamp=prediction_result.get("timestamp", time.time()),
            risk_score=prediction_result.get("risk_score", 0.0),
            risk_level=prediction_result.get("risk_level", "LOW"),
            probability=prediction_result.get("probability", 0.0),
            prediction=prediction_result.get("prediction", 0),
            label=prediction_result.get("label", "BENIGN"),
            features=prediction_result.get("raw_features", {}),
            reasons=prediction_result.get("reasons", []),
            mitre_techniques=prediction_result.get("mitre_techniques", []),
        )
        self._history.append(snapshot)
        logger.debug(
            f"Risk recorded: level={snapshot.risk_level} score={snapshot.risk_score:.4f}"
        )
        return snapshot

    def get_current_risk_level(self) -> str:
        """Return the most recent risk level."""
        if not self._history:
            return "LOW"
        return self._history[-1].risk_level

    def get_trending_risk_score(self) -> float:
        """
        Compute the mean risk score over the recent trend window.

        Returns:
            Mean risk score over the last N snapshots
        """
        recent = list(self._history)[-self.trend_window:]
        if not recent:
            return 0.0
        return sum(s.risk_score for s in recent) / len(recent)

    def is_escalating(self) -> bool:
        """
        Detect whether risk is escalating (positive trend).

        Returns:
            True if recent risk scores are trending upward
        """
        recent = list(self._history)[-self.trend_window:]
        if len(recent) < 3:
            return False

        scores = [s.risk_score for s in recent]
        # Simple linear trend: check if slope is positive
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = sum(scores) / n
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return False

        slope = numerator / denominator
        return slope > 0.01  # positive trend threshold

    def is_sustained_threat(self, threshold: float = 0.6, window: int = 5) -> bool:
        """
        Determine if risk has been sustained above threshold for N windows.

        Args:
            threshold: Risk score threshold
            window: Number of consecutive windows required

        Returns:
            True if sustained threat detected
        """
        recent = list(self._history)[-window:]
        if len(recent) < window:
            return False
        return all(s.risk_score >= threshold for s in recent)

    def get_peak_risk(self) -> float:
        """Return the highest risk score in history."""
        if not self._history:
            return 0.0
        return max(s.risk_score for s in self._history)

    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive risk summary.

        Returns:
            Dictionary with current, trending, peak, and status information
        """
        history_list = list(self._history)
        if not history_list:
            return {
                "current_risk_level": "LOW",
                "current_risk_score": 0.0,
                "trending_risk_score": 0.0,
                "peak_risk_score": 0.0,
                "is_escalating": False,
                "is_sustained_threat": False,
                "total_alerts": 0,
                "ransomware_detections": 0,
            }

        return {
            "current_risk_level": self.get_current_risk_level(),
            "current_risk_score": round(history_list[-1].risk_score, 4),
            "trending_risk_score": round(self.get_trending_risk_score(), 4),
            "peak_risk_score": round(self.get_peak_risk(), 4),
            "is_escalating": self.is_escalating(),
            "is_sustained_threat": self.is_sustained_threat(),
            "total_alerts": sum(
                1 for s in history_list if s.risk_score >= self.config.low_risk_max
            ),
            "ransomware_detections": sum(
                1 for s in history_list if s.prediction == 1
            ),
        }

    def clear_history(self) -> None:
        """Clear the risk snapshot history."""
        self._history.clear()
        logger.info("Risk history cleared.")