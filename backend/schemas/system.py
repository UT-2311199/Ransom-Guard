from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CPUInfo(BaseModel):
    percent: float = Field(..., description="CPU usage percentage")
    count_logical: int = Field(..., description="Number of logical CPU cores")
    count_physical: int = Field(..., description="Number of physical CPU cores")
    frequency_current: Optional[float] = Field(None, description="Current CPU frequency in MHz")
    frequency_max: Optional[float] = Field(None, description="Maximum CPU frequency in MHz")
    per_core_percent: List[float] = Field(default_factory=list, description="Per-core CPU usage")


class MemoryInfo(BaseModel):
    total: int = Field(..., description="Total memory in bytes")
    available: int = Field(..., description="Available memory in bytes")
    used: int = Field(..., description="Used memory in bytes")
    percent: float = Field(..., description="Memory usage percentage")
    total_gb: float = Field(..., description="Total memory in GB")
    used_gb: float = Field(..., description="Used memory in GB")
    available_gb: float = Field(..., description="Available memory in GB")


class DiskPartition(BaseModel):
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float
    total_gb: float
    used_gb: float
    free_gb: float


class DiskInfo(BaseModel):
    partitions: List[DiskPartition] = Field(default_factory=list)
    read_bytes: int = Field(0, description="Total bytes read")
    write_bytes: int = Field(0, description="Total bytes written")
    read_count: int = Field(0, description="Total read operations")
    write_count: int = Field(0, description="Total write operations")


class NetworkInfo(BaseModel):
    bytes_sent: int = Field(0)
    bytes_recv: int = Field(0)
    packets_sent: int = Field(0)
    packets_recv: int = Field(0)
    connections_count: int = Field(0)


class SystemInfo(BaseModel):
    hostname: str
    platform: str
    platform_version: str
    architecture: str
    boot_time: datetime
    uptime_seconds: float
    cpu: CPUInfo
    memory: MemoryInfo
    disk: DiskInfo
    network: NetworkInfo
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemResponse(BaseModel):
    success: bool = True
    data: SystemInfo
    timestamp: datetime = Field(default_factory=datetime.utcnow)