# ml/advanced/threat_timeline.py

import json
import os
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Deque, Dict, List, Optional

from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, MonitoringConfig

logger = get_logger(__name__)


@dataclass
class ThreatEvent:
    """Represents a single threat event in the timeline."""
    event_id: int
    timestamp: float
    event_type: str           # 'prediction', 'alert', 'quarantine', 'kill', 'escalation'
    risk_level: str
    risk_score: float
    label: str
    probability: float
    description: str
    features: Dict[str, float] = field(default_factory=dict)
    mitre_techniques: List[Dict] = field(default_factory=list)
    response_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ThreatTimeline:
    """
    Maintains a chronological threat event timeline.
    Supports querying, filtering, exporting, and pattern detection.
    """

    def __init__(
        self,
        monitoring_config: Optional[MonitoringConfig] = None,
        export_dir: Optional[str] = None,
    ):
        self.config = monitoring_config or CONFIG.monitoring
        self.export_dir = export_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "threat_reports",
        )
        os.makedirs(self.export_dir, exist_ok=True)

        self._events: Deque[ThreatEvent] = deque(
            maxlen=self.config.timeline_max_events
        )
        self._event_counter = 0

    # ------------------------------------------------------------------
    # Event Recording
    # ------------------------------------------------------------------

    def record_prediction(
        self,
        prediction_result: Dict[str, Any],
        response_actions: Optional[List[str]] = None,
    ) -> ThreatEvent:
        """
        Record a prediction result as a timeline event.

        Args:
            prediction_result: Output from RansomwarePredictor.predict()
            response_actions: List of automated responses taken

        Returns:
            Created ThreatEvent
        """
        event_type = "alert" if prediction_result.get("alert") else "prediction"
        self._event_counter += 1

        description = self._build_description(prediction_result)

        event = ThreatEvent(
            event_id=self._event_counter,
            timestamp=prediction_result.get("timestamp", time.time()),
            event_type=event_type,
            risk_level=prediction_result.get("risk_level", "LOW"),
            risk_score=prediction_result.get("risk_score", 0.0),
            label=prediction_result.get("label", "BENIGN"),
            probability=prediction_result.get("probability", 0.0),
            description=description,
            features=prediction_result.get("raw_features", {}),
            mitre_techniques=prediction_result.get("mitre_techniques", []),
            response_actions=response_actions or [],
            metadata={
                "model_used": prediction_result.get("model_used"),
                "reasons": prediction_result.get("reasons", []),
            },
        )

        self._events.append(event)
        logger.debug(
            f"Timeline event #{self._event_counter}: [{event.event_type}] "
            f"{event.label} | {event.risk_level}"
        )
        return event

    def record_action(
        self,
        action_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ThreatEvent:
        """
        Record a response action (kill, quarantine, backup) as an event.

        Args:
            action_type: Type of action ('kill', 'quarantine', 'backup')
            description: Human-readable description
            metadata: Additional action metadata

        Returns:
            Created ThreatEvent
        """
        self._event_counter += 1
        event = ThreatEvent(
            event_id=self._event_counter,
            timestamp=time.time(),
            event_type=action_type,
            risk_level="CRITICAL",
            risk_score=1.0,
            label="RESPONSE",
            probability=1.0,
            description=description,
            metadata=metadata or {},
        )
        self._events.append(event)
        return event

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_all_events(self) -> List[ThreatEvent]:
        """Return all timeline events."""
        return list(self._events)

    def get_alerts(self) -> List[ThreatEvent]:
        """Return only alert-level events."""
        return [e for e in self._events if e.event_type in ("alert", "kill", "quarantine")]

    def get_ransomware_events(self) -> List[ThreatEvent]:
        """Return events where ransomware was predicted."""
        return [e for e in self._events if e.label == "RANSOMWARE"]

    def get_events_by_risk_level(self, risk_level: str) -> List[ThreatEvent]:
        """Filter events by risk level (LOW, MEDIUM, HIGH, CRITICAL)."""
        return [e for e in self._events if e.risk_level == risk_level]

    def get_events_in_window(
        self, start_time: float, end_time: Optional[float] = None
    ) -> List[ThreatEvent]:
        """Return events within a time window."""
        end_time = end_time or time.time()
        return [
            e for e in self._events
            if start_time <= e.timestamp <= end_time
        ]

    def get_event_count(self) -> int:
        """Return total number of recorded events."""
        return len(self._events)

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the threat timeline."""
        events = list(self._events)
        if not events:
            return {"total_events": 0, "ransomware_detections": 0, "alerts": 0}

        return {
            "total_events": len(events),
            "ransomware_detections": sum(1 for e in events if e.label == "RANSOMWARE"),
            "alerts": sum(1 for e in events if e.event_type == "alert"),
            "kills": sum(1 for e in events if e.event_type == "kill"),
            "quarantines": sum(1 for e in events if e.event_type == "quarantine"),
            "critical_events": sum(1 for e in events if e.risk_level == "CRITICAL"),
            "first_event_time": events[0].timestamp,
            "last_event_time": events[-1].timestamp,
            "unique_mitre_techniques": list(
                {
                    t["technique_id"]
                    for e in events
                    for t in e.mitre_techniques
                }
            ),
        }

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_json(self, filename: Optional[str] = None) -> str:
        """
        Export the timeline to a JSON report file.

        Args:
            filename: Output filename (auto-generated if None)

        Returns:
            Path to the exported file
        """
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"threat_timeline_{timestamp}.json"

        path = os.path.join(self.export_dir, filename)

        report = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "summary": self.get_summary(),
            "events": [asdict(e) for e in self._events],
        }

        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Threat timeline exported: {path}")
        return path

    def export_csv(self, filename: Optional[str] = None) -> str:
        """
        Export timeline events to CSV.

        Args:
            filename: Output filename (auto-generated if None)

        Returns:
            Path to the exported file
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for CSV export.")

        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"threat_timeline_{timestamp}.csv"

        path = os.path.join(self.export_dir, filename)
        events = self.get_all_events()

        rows = []
        for e in events:
            row = {
                "event_id": e.event_id,
                "timestamp": e.timestamp,
                "datetime": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(e.timestamp)
                ),
                "event_type": e.event_type,
                "risk_level": e.risk_level,
                "risk_score": e.risk_score,
                "label": e.label,
                "probability": e.probability,
                "description": e.description,
                "mitre_count": len(e.mitre_techniques),
            }
            rows.append(row)

        pd.DataFrame(rows).to_csv(path, index=False)
        logger.info(f"Timeline CSV exported: {path}")
        return path

    def clear(self) -> None:
        """Clear all timeline events."""
        self._events.clear()
        logger.info("Threat timeline cleared.")

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_description(self, prediction_result: Dict[str, Any]) -> str:
        """Build a concise event description from prediction result."""
        label = prediction_result.get("label", "BENIGN")
        prob = prediction_result.get("probability", 0.0)
        level = prediction_result.get("risk_level", "LOW")
        reasons = prediction_result.get("reasons", [])

        desc = f"[{level}] {label} detected (probability={prob:.2%})"
        if reasons:
            desc += f" — {reasons[0][:80]}"
        return desc