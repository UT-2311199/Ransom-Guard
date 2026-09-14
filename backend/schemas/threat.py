from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ThreatStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    QUARANTINED = "quarantined"
    FALSE_POSITIVE = "false_positive"
    INVESTIGATING = "investigating"


class ThreatLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatLog(BaseModel):
    threat_id: Optional[str] = None
    file_path: str
    file_name: str
    file_extension: Optional[str] = None
    threat_level: ThreatLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=100.0)
    is_ransomware: bool
    indicators: List[str] = Field(default_factory=list)
    process_name: Optional[str] = None
    process_id: Optional[int] = None
    event_type: Optional[str] = None
    status: ThreatStatus = ThreatStatus.ACTIVE
    recommended_action: str
    action_taken: Optional[str] = None
    features: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None


class ThreatLogResponse(BaseModel):
    success: bool = True
    total: int
    threats: List[ThreatLog]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ThreatSummary(BaseModel):
    total_threats: int
    active_threats: int
    resolved_threats: int
    quarantined_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    safe_count: int
    ransomware_detected: int
    last_threat_at: Optional[datetime] = None