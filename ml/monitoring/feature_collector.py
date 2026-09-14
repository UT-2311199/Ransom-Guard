# ml/monitoring/feature_collector.py

import threading
import time
from collections import deque
from typing import Any, Callable, Dict, List, Optional

from ml.feature_extractor.extractor import FeatureExtractor
from ml.monitoring.file_monitor import FileSystemMonitor
from ml.monitoring.process_monitor import ProcessMonitor
from ml.predictor.predictor import RansomwarePredictor
from ml.utils.logger import get_logger
from ml.utils.config import CONFIG, MonitoringConfig

logger = get_logger(__name__)


class FeatureCollector:
    """
    Orchestrates file system monitoring, process monitoring,
    and periodic feature extraction + prediction.

    Flow:
        FileSystemMonitor -> FeatureExtractor <- ProcessMonitor
                                    |
                                    v
                          RansomwarePredictor
                                    |
                                    v
                          alert_callback / result_queue
    """

    def __init__(
        self,
        predictor: RansomwarePredictor,
        monitoring_config: Optional[MonitoringConfig] = None,
        alert_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        watch_directory: Optional[str] = None,
    ):
        self.predictor = predictor
        self.config = monitoring_config or CONFIG.monitoring
        self.alert_callback = alert_callback
        self.watch_directory = watch_directory or self.config.watch_directory

        # Core components
        self.extractor = FeatureExtractor(
            monitoring_config=self.config,
            window_seconds=self.config.feature_window,
        )

        self.file_monitor = FileSystemMonitor(
            extractor=self.extractor,
            monitoring_config=self.config,
            alert_callback=self._handle_file_alert,
        )

        self.process_monitor = ProcessMonitor(
            extractor=self.extractor,
            monitoring_config=self.config,
            alert_callback=self._handle_process_alert,
        )

        # State
        self._running = False
        self._stop_event = threading.Event()
        self._collection_thread: Optional[threading.Thread] = None

        # Result history
        self._prediction_history: deque = deque(
            maxlen=self.config.timeline_max_events
        )
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start all monitors and the periodic collection loop."""
        if self._running:
            logger.warning("FeatureCollector already running.")
            return

        logger.info("Starting RansomGuard monitoring system...")

        # Ensure predictor is loaded
        if not self.predictor._loaded:
            self.predictor.load()

        # Start file system monitoring
        self.file_monitor.start(watch_path=self.watch_directory)

        # Start process monitoring
        self.process_monitor.start()

        # Start collection loop
        self._stop_event.clear()
        self._collection_thread = threading.Thread(
            target=self._collection_loop,
            name="RansomGuard-Collector",
            daemon=True,
        )
        self._collection_thread.start()
        self._running = True

        logger.info(
            f"Monitoring active | "
            f"watch={self.watch_directory} | "
            f"interval={self.config.collection_interval}s"
        )

    def stop(self) -> None:
        """Stop all monitors and the collection loop."""
        self._stop_event.set()

        if self._collection_thread and self._collection_thread.is_alive():
            self._collection_thread.join(timeout=10)

        self.file_monitor.stop()
        self.process_monitor.stop()

        self._running = False
        logger.info("RansomGuard monitoring stopped.")

    def is_running(self) -> bool:
        """Return whether collection is active."""
        return self._running

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def get_prediction_history(self) -> List[Dict[str, Any]]:
        """Return list of historical prediction results."""
        with self._lock:
            return list(self._prediction_history)

    def get_latest_prediction(self) -> Optional[Dict[str, Any]]:
        """Return the most recent prediction result."""
        with self._lock:
            if self._prediction_history:
                return self._prediction_history[-1]
            return None

    def get_alert_count(self) -> int:
        """Return count of predictions that triggered alerts."""
        with self._lock:
            return sum(1 for r in self._prediction_history if r.get("alert"))

    # ------------------------------------------------------------------
    # Private: Collection Loop
    # ------------------------------------------------------------------

    def _collection_loop(self) -> None:
        """
        Periodically extract features and run prediction.
        Runs in background thread.
        """
        logger.debug("Collection loop started.")

        while not self._stop_event.is_set():
            try:
                self._collect_and_predict()
            except Exception as exc:
                logger.error(f"Collection loop error: {exc}")

            self._stop_event.wait(timeout=self.config.collection_interval)

        logger.debug("Collection loop exited.")

    def _collect_and_predict(self) -> None:
        """Extract features, predict, store, and alert."""
        features = self.extractor.extract_features()

        # Add timestamp to features dict
        features["timestamp"] = time.time()

        try:
            result = self.predictor.predict(features)
            result["raw_features"] = features
            result["timestamp"] = features["timestamp"]

            # Store in history
            with self._lock:
                self._prediction_history.append(result)

            # Trigger alert if needed
            if result.get("alert") and self.alert_callback:
                self.alert_callback(result)

            # Reset extractor window for next collection period
            self.extractor.reset_window()

        except Exception as exc:
            logger.error(f"Prediction failed in collection loop: {exc}")

    # ------------------------------------------------------------------
    # Private: Alert Handlers
    # ------------------------------------------------------------------

    def _handle_file_alert(self, event_type: str, data: str) -> None:
        """Handle file-level alerts from the file monitor."""
        logger.warning(f"File alert [{event_type}]: {data}")

    def _handle_process_alert(self, event_type: str, data: Dict) -> None:
        """Handle process-level alerts from the process monitor."""
        logger.warning(
            f"Process alert [{event_type}]: "
            f"pid={data.get('pid')} name={data.get('name')} "
            f"cmd={data.get('cmdline', '')[:80]}"
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()