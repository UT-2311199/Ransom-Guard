from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FileEventType(str, Enum):
    CREATED = "created"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"
    OPENED = "opened"
    CLOSED = "closed"
    MOVED = "moved"


class FileEvent(BaseModel):
    event_id: Optional[str] = None
    event_type: FileEventType
    file_path: str = Field(..., description="Full path of the affected file")
    file_name: str = Field(..., description="Name of the file")
    file_extension: Optional[str] = None
    file_size: Optional[int] = None
    is_directory: bool = False
    src_path: Optional[str] = None
    dest_path: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    process_id: Optional[int] = None
    process_name: Optional[str] = None


class ProcessInfo(BaseModel):
    pid: int = Field(..., description="Process ID")
    name: str = Field(..., description="Process name")
    status: str = Field(..., description="Process status")
    cpu_percent: float = Field(0.0, description="CPU usage percentage")
    memory_percent: float = Field(0.0, description="Memory usage percentage")
    memory_rss: int = Field(0, description="Resident Set Size in bytes")
    memory_vms: int = Field(0, description="Virtual Memory Size in bytes")
    exe: Optional[str] = Field(None, description="Executable path")
    cmdline: Optional[List[str]] = Field(default_factory=list)
    create_time: Optional[datetime] = None
    username: Optional[str] = None
    parent_pid: Optional[int] = None
    parent_name: Optional[str] = None
    num_threads: int = 0
    num_fds: Optional[int] = None
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0
    connections: int = 0
    is_suspicious: bool = False
    suspicion_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MonitorStatus(BaseModel):
    is_active: bool
    watch_path: str
    events_captured: int
    start_time: Optional[datetime] = None
    uptime_seconds: float = 0.0


class FileEventsResponse(BaseModel):
    success: bool = True
    total: int
    events: List[FileEvent]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProcessListResponse(BaseModel):
    success: bool = True
    total: int
    processes: List[ProcessInfo]
    timestamp: datetime = Field(default_factory=datetime.utcnow)