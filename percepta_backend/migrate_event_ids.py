"""
migrate_event_ids.py — переименовывает все event_id в EVT-000001 формат.
Запусти ОДИН РАЗ из percepta_backend/:
    python migrate_event_ids.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.database import SessionLocal, Base, engine
from api import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    events = db.query(models.Event).order_by(models.Event.id).all()
    print(f"Found {len(events)} events. Renaming...")

    for i, event in enumerate(events, start=1):
        old_id = event.event_id
        new_id = f"EVT-{str(i).zfill(6)}"
        event.event_id = new_id
        print(f"  {old_id}  →  {new_id}")

    db.commit()
    print(f"\n✅ Done! All {len(events)} events renamed to EVT-XXXXXX format.")
finally:
    db.close()