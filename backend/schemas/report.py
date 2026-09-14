from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ReportType(str, Enum):
    THREAT_SUMMARY = "threat_summary"
    INCIDENT_REPORT = "incident_report"
    SYSTEM_STATUS = "system_status"
    FULL_AUDIT = "full_audit"


class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


class ReportRequest(BaseModel):
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_system_info: bool = True
    include_threats: bool = True
    include_processes: bool = True
    title: Optional[str] = None
    description: Optional[str] = None


class ReportMetadata(BaseModel):
    report_id: str
    title: str
    report_type: ReportType
    format: ReportFormat
    file_path: str
    file_name: str
    file_size: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    threat_count: int = 0
    generated_by: str = "RansomGuard System"


class ReportResponse(BaseModel):
    success: bool = True
    report: ReportMetadata
    download_url: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReportListResponse(BaseModel):
    success: bool = True
    total: int
    reports: List[ReportMetadata]
    timestamp: datetime = Field(default_factory=datetime.utcnow)