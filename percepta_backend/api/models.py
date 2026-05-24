"""SQLAlchemy ORM models for Percepta IDS/IPS backend."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from api.database import Base


class Event(Base):
    """Stores every IDS/IPS network event received from the ML engine."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    # --- Identification ---
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    # --- Network data ---
    source_ip = Column(String(45), index=True, nullable=False)
    destination_ip = Column(String(45), nullable=True)
    protocol = Column(String(10), nullable=True)
    destination_port = Column(Integer, nullable=True)

    # --- Flow characteristics ---
    flow_duration_ms = Column(Integer, nullable=True)
    total_packets = Column(Integer, nullable=True)
    total_bytes = Column(Integer, nullable=True)

    # --- ML level ---
    anomaly_score = Column(Float, nullable=False)
    adaptive_threshold = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, default=True, nullable=False)

    # --- Temporal stability ---
    anomaly_count_window = Column(Integer, nullable=True)
    max_consecutive_anomalies = Column(Integer, nullable=True)
    frequency_window = Column(Float, nullable=True)
    stability_score = Column(Float, nullable=True)

    # --- Context and risk ---
    network_load = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(10), index=True, nullable=False)

    # --- IPS actions ---
    action_taken = Column(String(20), nullable=False)
    action_duration_seconds = Column(Integer, nullable=True)
    block_expires_at = Column(DateTime, nullable=True)

    # --- System info ---
    system_mode = Column(String(20), default="ADAPTIVE", nullable=True)
    model_version = Column(String(20), default="IF_v1.0", nullable=True)


class BlockedIP(Base):
    """Tracks currently blocked IPs with escalation support."""

    __tablename__ = "blocked_ips"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, index=True, nullable=False)
    blocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    block_expires_at = Column(DateTime, nullable=True)
    strike_count = Column(Integer, default=1, nullable=False)
    current_risk_level = Column(String(10), default="CRITICAL", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    reason = Column(Text, nullable=True)


class UserSession(Base):
    """
    Tracks network user sessions for the Logs page.
    One row per unique IP per day.
    Created automatically when a new event arrives from a new IP.
    Updated on every subsequent event from the same IP (same day).
    """

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # Unique session identifier  e.g. "ses_000001"
    session_id = Column(String(32), index=True, nullable=False)

    # The IP address of this session
    ip_address = Column(String(45), index=True, nullable=False)

    # Day this session belongs to (date only, no time)  e.g. 2026-03-13
    session_date = Column(String(10), index=True, nullable=False)

    # First event time for this IP on this day
    login_time = Column(DateTime, nullable=False)

    # Last event time for this IP on this day (updated on every new event)
    logout_time = Column(DateTime, nullable=True)

    # Total bytes transferred (sum of total_bytes from all events)
    traffic_bytes = Column(Integer, default=0, nullable=False)

    # ACTIVE | ENDED
    status = Column(String(10), default="ACTIVE", nullable=False)