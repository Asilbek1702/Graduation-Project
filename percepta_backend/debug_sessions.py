"""
debug_sessions.py — показывает все события и сессии в БД.
Запусти из percepta_backend/:
    python debug_sessions.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.database import SessionLocal
from api import models

db = SessionLocal()

print("\n=== EVENTS ===")
events = db.query(models.Event).order_by(models.Event.timestamp).all()
print(f"Total: {len(events)}")
for e in events:
    dt = e.timestamp
    date_str = dt.strftime("%Y-%m-%d") if dt else "None"
    print(f"  {e.source_ip:<18} date={date_str}  time={dt}  action={e.action_taken}")

print("\n=== USER_SESSIONS ===")
sessions = db.query(models.UserSession).order_by(models.UserSession.login_time).all()
print(f"Total: {len(sessions)}")
for s in sessions:
    print(f"  {s.ip_address:<18} date={s.session_date}  login={s.login_time}  status={s.status}")

print("\n=== MISSING (events without session) ===")
session_keys = set()
for s in sessions:
    session_keys.add(f"{s.ip_address}_{s.session_date}")

missing = []
for e in events:
    dt = e.timestamp
    date_str = dt.strftime("%Y-%m-%d") if dt else "None"
    key = f"{e.source_ip}_{date_str}"
    if key not in session_keys:
        missing.append((e.source_ip, date_str, e.timestamp))
        print(f"  ❌ MISSING: ip={e.source_ip}  date={date_str}  timestamp={e.timestamp}")

if not missing:
    print("  ✅ No missing sessions found")

db.close()