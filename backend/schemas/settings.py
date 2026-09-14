from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class MonitorSettings(BaseModel):
    watch_path: str = Field("/", description="Path to monitor")
    enabled: bool = Field(True, description="Enable file monitoring")
    recursive: bool = Field(True, description="Monitor subdirectories")
    excluded_paths: List[str] = Field(
        default_factory=lambda: ["/proc", "/sys", "/dev"],
        description="Paths to exclude from monitoring"
    )
    file_extensions_whitelist: List[str] = Field(
        default_factory=list, description="Whitelist of file extensions"
    )


class AlertSettings(BaseModel):
    enable_alerts: bool = True
    threat_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence for alerting")
    auto_quarantine: bool = Field(False, description="Automatically quarantine threats")
    auto_terminate: bool = Field(False, description="Automatically terminate suspicious processes")
    alert_on_critical: bool = True
    alert_on_high: bool = True
    alert_on_medium: bool = False


class MLSettings(BaseModel):
    model_path: str = Field("models/ransomware_detector.joblib", description="Path to ML model")
    confidence_threshold: float = Field(0.6, ge=0.0, le=1.0)
    feature_extraction_enabled: bool = True
    entropy_analysis: bool = True
    behavioral_analysis: bool = True


class SystemSettings(BaseModel):
    log_retention_days: int = Field(30, ge=1, le=365)
    report_retention_days: int = Field(90, ge=1, le=365)
    max_log_size_mb: int = Field(100, ge=10, le=10000)
    timezone: str = "UTC"
    enable_system_monitoring: bool = True
    process_scan_interval: int = Field(5, ge=1, le=60, description="Seconds between process scans")


class AppSettings(BaseModel):
    monitor: MonitorSettings = Field(default_factory=MonitorSettings)
    alerts: AlertSettings = Field(default_factory=AlertSettings)
    ml: MLSettings = Field(default_factory=MLSettings)
    system: SystemSettings = Field(default_factory=SystemSettings)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SettingsUpdateRequest(BaseModel):
    monitor: Optional[MonitorSettings] = None
    alerts: Optional[AlertSettings] = None
    ml: Optional[MLSettings] = None
    system: Optional[SystemSettings] = None


class SettingsResponse(BaseModel):
    success: bool = True
    settings: AppSettings
    message: str = "Settings retrieved successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)