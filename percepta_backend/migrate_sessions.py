"""
migrate_sessions.py — Run once to populate user_sessions from existing events.

Place this file in percepta_backend/ and run:
    cd percepta_backend
    python migrate_sessions.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.database import SessionLocal, Base, engine
from api import models, schemas
from sqlalchemy import func
from datetime import datetime

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Get all existing events ordered by timestamp
    events = db.query(models.Event).order_by(models.Event.timestamp).all()
    print(f"Found {len(events)} events to process...")

    count = 0
    for event in events:
        event_dt = event.timestamp if event.timestamp else datetime.utcnow()
        session_date = event_dt.strftime("%Y-%m-%d")
        bytes_this = event.total_bytes or 0

        record = db.query(models.UserSession).filter(
            models.UserSession.ip_address == event.source_ip,
            models.UserSession.session_date == session_date,
        ).first()

        if record:
            if event_dt > record.logout_time if record.logout_time else True:
                record.logout_time = event_dt
            record.traffic_bytes += bytes_this
            if event.action_taken == "TEMP_BLOCK":
                record.status = "ENDED"
        else:
            total_count = db.query(func.count(models.UserSession.id)).scalar() or 0
            session_id = f"ses_{str(total_count + 1).zfill(6)}"
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
            count += 1

        db.commit()

    total = db.query(func.count(models.UserSession.id)).scalar()
    print(f"✅ Done! Created {count} new sessions. Total in DB: {total}")

finally:
    db.close()