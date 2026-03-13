"""Pydantic schemas for Percepta API — matches the agreed API contract."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
#  EVENT SCHEMAS
# ─────────────────────────────────────────────

class EventCreate(BaseModel):
    """Schema for POST /api/events — sent by the ML engine."""

    event_id: str = Field(..., example="evt_20260212_001245")
    timestamp: datetime = Field(..., example="2026-02-12T14:05:10Z")

    # Network data
    source_ip: str = Field(..., example="192.168.1.15")
    destination_ip: Optional[str] = Field(None, example="10.0.0.5")
    protocol: Optional[str] = Field(None, example="TCP")
    destination_port: Optional[int] = Field(None, example=443)

    # Flow characteristics
    flow_duration_ms: Optional[int] = Field(None, example=1200)
    total_packets: Optional[int] = Field(None, example=45)
    total_bytes: Optional[int] = Field(None, example=18200)

    # ML level
    anomaly_score: float = Field(..., ge=0.0, le=1.0, example=0.22)
    adaptive_threshold: float = Field(..., ge=0.0, le=1.0, example=0.68)
    is_anomaly: bool = Field(..., example=True)

    # Temporal stability
    anomaly_count_window: Optional[int] = Field(None, example=6)
    max_consecutive_anomalies: Optional[int] = Field(None, example=4)
    frequency_window: Optional[float] = Field(None, example=0.20)
    stability_score: Optional[float] = Field(None, example=0.74)

    # Context and risk
    network_load: Optional[float] = Field(None, ge=0.0, le=1.0, example=0.80)
    risk_score: float = Field(..., ge=0.0, le=1.0, example=0.65)
    risk_level: str = Field(..., example="HIGH")

    # IPS actions
    action_taken: str = Field(..., example="RATE_LIMIT")
    action_duration_seconds: Optional[int] = Field(None, example=60)
    block_expires_at: Optional[datetime] = Field(None)

    # System info
    system_mode: Optional[str] = Field("ADAPTIVE", example="ADAPTIVE")
    model_version: Optional[str] = Field("IF_v1.0", example="IF_v1.0")


class EventResponse(BaseModel):
    """Full event object returned by the API."""

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

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  BLOCKED IP SCHEMAS
# ─────────────────────────────────────────────

class BlockedIPResponse(BaseModel):
    id: int
    ip_address: str
    blocked_at: datetime
    block_expires_at: Optional[datetime]
    strike_count: int
    current_risk_level: str
    is_active: bool
    reason: Optional[str]

    class Config:
        from_attributes = True


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
