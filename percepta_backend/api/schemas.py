"""Pydantic schemas for Percepta API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────
#  EVENT SCHEMAS
# ─────────────────────────────────────────────

class EventCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    event_id: str = Field(..., example="evt_20260212_001245")
    timestamp: datetime = Field(..., example="2026-02-12T14:05:10Z")
    source_ip: str = Field(..., example="192.168.1.15")
    destination_ip: Optional[str] = Field(None)
    protocol: Optional[str] = Field(None)
    destination_port: Optional[int] = Field(None)
    flow_duration_ms: Optional[int] = Field(None)
    total_packets: Optional[int] = Field(None)
    total_bytes: Optional[int] = Field(None)
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    adaptive_threshold: float = Field(..., ge=0.0, le=1.0)
    is_anomaly: bool = Field(...)
    anomaly_count_window: Optional[int] = Field(None)
    max_consecutive_anomalies: Optional[int] = Field(None)
    frequency_window: Optional[float] = Field(None)
    stability_score: Optional[float] = Field(None)
    network_load: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str = Field(...)
    action_taken: str = Field(...)
    action_duration_seconds: Optional[int] = Field(None)
    block_expires_at: Optional[datetime] = Field(None)
    system_mode: Optional[str] = Field("ADAPTIVE")
    model_version: Optional[str] = Field("IF_v1.0")


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    event_id: str
    timestamp: datetime
    source_ip: str
    destination_ip: Optional[str]
    protocol: Optional[str]
    destination_port: Optional[int]
    flow_duration_ms: Optional[int]
    total_packets: Optional[int]
    total_bytes: Optional[int]
    anomaly_score: float
    adaptive_threshold: float
    is_anomaly: bool
    anomaly_count_window: Optional[int]
    max_consecutive_anomalies: Optional[int]
    frequency_window: Optional[float]
    stability_score: Optional[float]
    network_load: Optional[float]
    risk_score: float
    risk_level: str
    action_taken: str
    action_duration_seconds: Optional[int]
    block_expires_at: Optional[datetime]
    system_mode: Optional[str]
    model_version: Optional[str]


# ─────────────────────────────────────────────
#  BLOCKED IP SCHEMAS
# ─────────────────────────────────────────────

class BlockedIPResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_address: str
    blocked_at: datetime
    block_expires_at: Optional[datetime]
    strike_count: int
    current_risk_level: str
    is_active: bool
    reason: Optional[str]


class IPStatusResponse(BaseModel):
    ip: str
    is_blocked: bool
    block_expires_at: Optional[datetime]
    strike_count: int
    current_risk_level: str


# ─────────────────────────────────────────────
#  STATS SCHEMA
# ─────────────────────────────────────────────

class RiskDistribution(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class StatsResponse(BaseModel):
    total_flows: int
    total_anomalies: int
    risk_distribution: RiskDistribution
    blocked_ips: int
    current_network_load: float


# ─────────────────────────────────────────────
#  USER SESSION SCHEMAS
# ─────────────────────────────────────────────

class UserSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    ip_address: str
    session_date: str
    login_time: datetime
    logout_time: Optional[datetime]
    traffic_bytes: int
    status: str