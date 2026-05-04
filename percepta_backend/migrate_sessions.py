"""
migrate_sessions.py — заполняет user_sessions из events + исправляет session_id на EVT формат.
Запусти из percepta_backend/:
    python migrate_sessions.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.database import SessionLocal, Base, engine
from api import models
from sqlalchemy import func, asc

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    events = db.query(models.Event).order_by(models.Event.timestamp).all()
    print(f"Found {len(events)} events to process...")

    created = 0
    for event in events:
        event_dt     = event.timestamp
        session_date = event_dt.strftime("%Y-%m-%d")
        bytes_this   = event.total_bytes or 0

        record = db.query(models.UserSession).filter(
            models.UserSession.ip_address == event.source_ip,
            models.UserSession.session_date == session_date,
        ).first()

        if record:
            if record.logout_time is None or event_dt > record.logout_time:
                record.logout_time = event_dt
            record.traffic_bytes += bytes_this
        else:
            count      = db.query(func.count(models.UserSession.id)).scalar() or 0
            session_id = f"ses_{str(count + 1).zfill(6)}"
            record = models.UserSession(
                session_id=session_id,
                ip_address=event.source_ip,
                session_date=session_date,
                login_time=event_dt,
                logout_time=event_dt,
                traffic_bytes=bytes_this,
                status="ACTIVE",
            )
            db.add(record)
            created += 1

        db.commit()

    # Now update session_id to match EVT-XXXXXX of first event per session
    print("\nUpdating session IDs to match EVT-XXXXXX format...")
    sessions = db.query(models.UserSession).order_by(models.UserSession.login_time).all()
    updated = 0
    for s in sessions:
        first_event = (
            db.query(models.Event)
            .filter(
                models.Event.source_ip == s.ip_address,
                func.date(models.Event.timestamp) == s.session_date,
            )
            .order_by(asc(models.Event.timestamp))
            .first()
        )
        if not first_event:
            first_event = (
                db.query(models.Event)
                .filter(models.Event.source_ip == s.ip_address)
                .order_by(asc(models.Event.timestamp))
                .first()
            )
        if first_event and not s.session_id.startswith("EVT-"):
            old_id = s.session_id
            s.session_id = first_event.event_id
            print(f"  {old_id}  →  {s.session_id}  ({s.ip_address})")
            updated += 1

    db.commit()

    total = db.query(func.count(models.UserSession.id)).scalar()
    print(f"\n✅ Done! Created {created} new sessions, updated {updated} IDs. Total: {total}")

finally:
    db.close()