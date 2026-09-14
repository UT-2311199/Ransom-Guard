from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ThreatLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PredictionRequest(BaseModel):
    file_path: str = Field(..., description="Full path to the file being analyzed")
    file_name: Optional[str] = Field(None, description="Name of the file")
    file_extension: Optional[str] = Field(None, description="File extension")
    file_size: Optional[int] = Field(None, description="File size in bytes", ge=0)
    entropy: Optional[float] = Field(None, description="File entropy value", ge=0.0, le=8.0)
    process_name: Optional[str] = Field(None, description="Associated process name")
    process_id: Optional[int] = Field(None, description="Associated process ID")
    event_type: Optional[str] = Field(None, description="File system event type")
    rapid_changes: Optional[int] = Field(0, description="Number of rapid file changes", ge=0)
    extensions_modified: Optional[List[str]] = Field(
        default_factory=list, description="List of extensions modified"
    )
    suspicious_keywords: Optional[List[str]] = Field(
        default_factory=list, description="Suspicious keywords found"
    )

    @validator("file_path")
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError("file_path cannot be empty")
        return v.strip()


class PredictionResult(BaseModel):
    prediction_id: str
    file_path: str
    file_name: str
    threat_level: ThreatLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_ransomware: bool
    risk_score: float = Field(..., ge=0.0, le=100.0)
    features_analyzed: Dict[str, Any] = Field(default_factory=dict)
    indicators: List[str] = Field(default_factory=list)
    recommended_action: str
    model_version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PredictionResponse(BaseModel):
    success: bool = True
    result: PredictionResult
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TerminateRequest(BaseModel):
    pid: int = Field(..., description="Process ID to terminate", gt=0)
    reason: Optional[str] = Field(None, description="Reason for termination")
    force: bool = Field(False, description="Force kill if normal termination fails")


class QuarantineRequest(BaseModel):
    file_path: str = Field(..., description="Full path of file to quarantine")
    threat_id: Optional[str] = Field(None, description="Associated threat log ID")
    reason: Optional[str] = Field(None, description="Reason for quarantine")

    @validator("file_path")
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError("file_path cannot be empty")
        return v.strip()