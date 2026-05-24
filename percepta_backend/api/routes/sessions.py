"""Sessions routes: GET /api/sessions, GET /api/sessions/today, GET /api/sessions/export"""

from datetime import datetime
from typing import List, Optional
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, func

from api.database import get_db
from api import crud, schemas, models

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


def _enrich_sessions(sessions: list, db: Session) -> list:
    """
    For each session attach the event_id of the FIRST event from that IP
    on that session_date. Both Events page and Logs page show the same EVT-XXXXXX.
    """
    result = []
    for s in sessions:
        # Filter strictly by session_date (YYYY-MM-DD string match on date part)
        # Get the LATEST event from this IP on this day
        # (same ordering as Events page — newest first)
        # Get the latest event for this IP (no date filter — avoids timezone issues)
        # This matches what the Events page shows for this IP at the top
        latest_event = (
            db.query(models.Event)
            .filter(models.Event.source_ip == s.ip_address)
            .order_by(desc(models.Event.id))
            .first()
        )

        event_id = latest_event.event_id if latest_event else f"EVT-{str(s.id).zfill(6)}"

        row = {
            "id":            s.id,
            "session_id":    s.session_id,
            "event_id":      event_id,
            "ip_address":    s.ip_address,
            "session_date":  s.session_date,
            "login_time":    s.login_time,
            "logout_time":   s.logout_time,
            "traffic_bytes": s.traffic_bytes,
            "status":        s.status,
        }
        result.append(row)
    return result


@router.get("/")
def get_sessions(
    limit: int = Query(200, ge=1, le=1000),
    session_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    sessions = crud.get_sessions(db, limit=limit, session_date=session_date)
    return _enrich_sessions(sessions, db)


@router.get("/today")
def get_sessions_today(db: Session = Depends(get_db)):
    sessions = crud.get_sessions_today(db)
    return _enrich_sessions(sessions, db)


@router.get("/export")
def export_sessions_today(db: Session = Depends(get_db)):
    """Export today's sessions as Excel. Columns include real event_id."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return {"error": "openpyxl not installed. Run: pip install openpyxl"}

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    sessions  = crud.get_sessions_today(db)
    enriched  = _enrich_sessions(sessions, db)

    def get_latest_event(ip: str):
        return (
            db.query(models.Event)
            .filter(models.Event.source_ip == ip)
            .order_by(models.Event.timestamp.desc())
            .first()
        )

    def fmt_time(dt):
        return dt.strftime("%H:%M:%S") if dt else "—"

    def fmt_duration(login, logout):
        if not login or not logout:
            return "—"
        diff = max(0, int((logout - login).total_seconds()))
        h, rem = divmod(diff, 3600)
        m, s   = divmod(rem, 60)
        return f"{h}h {m}m" if h > 0 else (f"{m}m {s}s" if m > 0 else f"{s}s")

    def fmt_bytes(b):
        if not b:
            return "0 B"
        if b >= 1_073_741_824: return f"{b/1_073_741_824:.2f} GB"
        if b >= 1_048_576:     return f"{b/1_048_576:.1f} MB"
        if b >= 1024:          return f"{b/1024:.1f} KB"
        return f"{b} B"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Sessions {today_str}"

    header_fill = PatternFill("solid", fgColor="1a2235")
    header_font = Font(bold=True, color="22d3ee", size=11)

    headers    = ["Event ID", "IP Address", "Login Time", "Logout Time",
                  "Duration", "Traffic Used", "Destination",
                  "Anomaly Score", "Stability Score", "Network Load", "Risk Level"]
    col_widths = [26, 16, 12, 12, 12, 14, 20, 14, 16, 14, 12]

    for ci, (h, w) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=ci, value=h)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[cell.column_letter].width = w
    ws.row_dimensions[1].height = 20

    for ri, s in enumerate(enriched, start=2):
        evt = get_latest_event(s["ip_address"])
        row_data = [
            s["event_id"],
            s["ip_address"],
            fmt_time(s["login_time"]),
            fmt_time(s["logout_time"]) if s["status"] == "ENDED" else "— online —",
            fmt_duration(s["login_time"], s["logout_time"]),
            fmt_bytes(s["traffic_bytes"]),
            f"{evt.destination_ip}:{evt.destination_port}" if evt and evt.destination_ip else "—",
            round(evt.anomaly_score, 4)   if evt else "—",
            round(evt.stability_score, 4) if evt and evt.stability_score else "—",
            round(evt.network_load, 4)    if evt and evt.network_load else "—",
            evt.risk_level if evt else "—",
        ]
        for ci, val in enumerate(row_data, start=1):
            cell = ws.cell(row=ri, column=ci, value=val)
            cell.alignment = Alignment(horizontal="left", vertical="center")
            if ri % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="161d2e")
        ws.row_dimensions[ri].height = 16

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"sessions_{today_str}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )