"""CRUD operations for Percepta IDS/IPS backend."""

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from api import models, schemas


# ─────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────

def create_event(db: Session, event: schemas.EventCreate) -> models.Event:
    """Insert a new event. Also updates BlockedIP and UserSession tables."""

    db_event = models.Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Auto-manage BlockedIP table
    if event.action_taken == "TEMP_BLOCK":
        _upsert_blocked_ip(db, event)

    # Auto-manage UserSession table
    _upsert_user_session(db, event)

    return db_event


def get_events(
    db: Session,
    limit: int = 100,
    risk_level: Optional[str] = None,
    source_ip: Optional[str] = None,
) -> List[models.Event]:
    """Return latest events with optional filters."""

    query = db.query(models.Event)
    if risk_level:
        query = query.filter(models.Event.risk_level == risk_level.upper())
    if source_ip:
        query = query.filter(models.Event.source_ip == source_ip)
    return query.order_by(desc(models.Event.timestamp)).limit(limit).all()


def get_event_by_id(db: Session, event_id: str) -> Optional[models.Event]:
    """Return a single event by its event_id string."""
    return db.query(models.Event).filter(models.Event.event_id == event_id).first()


# ─────────────────────────────────────────────
#  STATS
# ─────────────────────────────────────────────

def get_stats(db: Session) -> schemas.StatsResponse:
    """Compute dashboard stats from the events table."""

    total_flows = db.query(func.count(models.Event.id)).scalar() or 0
    total_anomalies = db.query(func.count(models.Event.id)).filter(
        models.Event.is_anomaly == True
    ).scalar() or 0

    risk_counts = (
        db.query(models.Event.risk_level, func.count(models.Event.id))
        .group_by(models.Event.risk_level)
        .all()
    )
    dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for level, count in risk_counts:
        if level in dist:
            dist[level] = count

    blocked_ips = db.query(func.count(models.BlockedIP.id)).filter(
        models.BlockedIP.is_active == True
    ).scalar() or 0

    avg_load = db.query(func.avg(models.Event.network_load)).scalar() or 0.0

    return schemas.StatsResponse(
        total_flows=total_flows,
        total_anomalies=total_anomalies,
        risk_distribution=schemas.RiskDistribution(
            low=dist["LOW"],
            medium=dist["MEDIUM"],
            high=dist["HIGH"],
            critical=dist["CRITICAL"],
        ),
        blocked_ips=blocked_ips,
        current_network_load=round(float(avg_load), 3),
    )


# ─────────────────────────────────────────────
#  BLOCKED IPs
# ─────────────────────────────────────────────

def get_blocked_ips(db: Session) -> List[models.BlockedIP]:
    """Return all currently active blocked IPs."""
    return (
        db.query(models.BlockedIP)
        .filter(models.BlockedIP.is_active == True)
        .order_by(desc(models.BlockedIP.blocked_at))
        .all()
    )


def get_ip_status(db: Session, ip_address: str) -> schemas.IPStatusResponse:
    """Return block status for a specific IP."""
    record = db.query(models.BlockedIP).filter(
        models.BlockedIP.ip_address == ip_address
    ).first()

    if not record or not record.is_active:
        return schemas.IPStatusResponse(
            ip=ip_address,
            is_blocked=False,
            block_expires_at=None,
            strike_count=record.strike_count if record else 0,
            current_risk_level="LOW",
        )

    return schemas.IPStatusResponse(
        ip=ip_address,
        is_blocked=True,
        block_expires_at=record.block_expires_at,
        strike_count=record.strike_count,
        current_risk_level=record.current_risk_level,
    )


def unblock_ip(db: Session, ip_address: str) -> bool:
    """Mark a blocked IP as inactive (manual admin unblock)."""
    record = db.query(models.BlockedIP).filter(
        models.BlockedIP.ip_address == ip_address,
        models.BlockedIP.is_active == True,
    ).first()

    if not record:
        return False

    record.is_active = False
    db.commit()
    return True


# ─────────────────────────────────────────────
#  USER SESSIONS
# ─────────────────────────────────────────────

def get_sessions(
    db: Session,
    limit: int = 200,
    session_date: Optional[str] = None,
) -> List[models.UserSession]:
    """Return sessions ordered by login_time descending."""
    query = db.query(models.UserSession)
    if session_date:
        query = query.filter(models.UserSession.session_date == session_date)
    return query.order_by(desc(models.UserSession.login_time)).limit(limit).all()


def get_sessions_today(db: Session) -> List[models.UserSession]:
    """Return all sessions for today."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return (
        db.query(models.UserSession)
        .filter(models.UserSession.session_date == today)
        .order_by(desc(models.UserSession.login_time))
        .all()
    )


# ─────────────────────────────────────────────
#  INTERNAL HELPERS
# ─────────────────────────────────────────────

def _upsert_blocked_ip(db: Session, event: schemas.EventCreate) -> None:
    """Insert or update BlockedIP record when a TEMP_BLOCK action is taken."""
    record = db.query(models.BlockedIP).filter(
        models.BlockedIP.ip_address == event.source_ip
    ).first()

    if record:
        record.strike_count += 1
        record.blocked_at = datetime.utcnow()
        record.block_expires_at = event.block_expires_at
        record.current_risk_level = event.risk_level
        record.is_active = True
    else:
        record = models.BlockedIP(
            ip_address=event.source_ip,
            blocked_at=datetime.utcnow(),
            block_expires_at=event.block_expires_at,
            strike_count=1,
            current_risk_level=event.risk_level,
            is_active=True,
            reason=f"Auto-blocked: risk={event.risk_level}, score={event.risk_score}",
        )
        db.add(record)

    db.commit()


def _upsert_user_session(db: Session, event: schemas.EventCreate) -> None:
    """
    Create or update a UserSession row.
    One session per unique IP per calendar day (UTC).
    """
    event_dt = event.timestamp if event.timestamp else datetime.utcnow()
    session_date = event_dt.strftime("%Y-%m-%d")

    record = db.query(models.UserSession).filter(
        models.UserSession.ip_address == event.source_ip,
        models.UserSession.session_date == session_date,
    ).first()

    bytes_this_event = event.total_bytes or 0

    if record:
        # Update logout_time to latest event
        if event_dt > record.logout_time if record.logout_time else True:
            record.logout_time = event_dt
        record.traffic_bytes += bytes_this_event
        # Mark ENDED only if action is terminal (TEMP_BLOCK)
        # Otherwise keep ACTIVE
        if event.action_taken == "TEMP_BLOCK":
            record.status = "ENDED"
    else:
        # Count existing sessions to generate session_id
        count = db.query(func.count(models.UserSession.id)).scalar() or 0
        session_id = f"ses_{str(count + 1).zfill(6)}"

        record = models.UserSession(
            session_id=session_id,
            ip_address=event.source_ip,
            session_date=session_date,
            login_time=event_dt,
            logout_time=event_dt,
            traffic_bytes=bytes_this_event,
            status="ACTIVE",
        )
        db.add(record)

    db.commit()