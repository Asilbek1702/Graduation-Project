"""Sessions routes: GET /api/sessions, GET /api/sessions/today, GET /api/sessions/export"""

from datetime import datetime
from typing import List, Optional
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.database import get_db
from api import crud, schemas, models

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.get("/", response_model=List[schemas.UserSessionResponse])
def get_sessions(
    limit: int = Query(200, ge=1, le=1000),
    session_date: Optional[str] = Query(None, description="Filter by date YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """Return user sessions, newest first."""
    return crud.get_sessions(db, limit=limit, session_date=session_date)


@router.get("/today", response_model=List[schemas.UserSessionResponse])
def get_sessions_today(db: Session = Depends(get_db)):
    """Return all sessions for today (UTC)."""
    return crud.get_sessions_today(db)


@router.get("/export")
def export_sessions_today(db: Session = Depends(get_db)):
    """
    Export today's sessions as an Excel file.
    Columns: Event ID, IP Address, Login Time, Logout Time, Duration,
             Traffic Used, Destination, Anomaly Score, Stability Score,
             Network Load, Risk Level
    Button 'Export Today' calls this endpoint.
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return {"error": "openpyxl not installed. Run: pip install openpyxl"}

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    sessions = crud.get_sessions_today(db)

    # For each session, get the latest event from that IP today to pull ML fields
    def get_latest_event(ip: str):
        return (
            db.query(models.Event)
            .filter(
                models.Event.source_ip == ip,
                models.Event.timestamp >= today_str,
            )
            .order_by(models.Event.timestamp.desc())
            .first()
        )

    def fmt_time(dt):
        if not dt:
            return "—"
        return dt.strftime("%H:%M:%S")

    def fmt_duration(login, logout):
        if not login or not logout:
            return "—"
        diff = int((logout - login).total_seconds())
        if diff < 0:
            diff = 0
        h = diff // 3600
        m = (diff % 3600) // 60
        s = diff % 60
        if h > 0:
            return f"{h}h {m}m"
        if m > 0:
            return f"{m}m {s}s"
        return f"{s}s"

    def fmt_bytes(b):
        if not b:
            return "0 B"
        if b >= 1_073_741_824:
            return f"{b/1_073_741_824:.2f} GB"
        if b >= 1_048_576:
            return f"{b/1_048_576:.1f} MB"
        if b >= 1024:
            return f"{b/1024:.1f} KB"
        return f"{b} B"

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Sessions {today_str}"

    # Header style
    header_fill = PatternFill("solid", fgColor="1a2235")
    header_font = Font(bold=True, color="22d3ee", size=11)

    headers = [
        "Event ID", "IP Address", "Login Time", "Logout Time",
        "Duration", "Traffic Used", "Destination",
        "Anomaly Score", "Stability Score", "Network Load", "Risk Level"
    ]

    col_widths = [18, 16, 12, 12, 12, 14, 18, 14, 16, 14, 12]

    for col_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[cell.column_letter].width = width

    ws.row_dimensions[1].height = 20

    # Data rows
    for row_idx, session in enumerate(sessions, start=2):
        evt = get_latest_event(session.ip_address)

        destination = f"{evt.destination_ip}:{evt.destination_port}" if evt and evt.destination_ip else "—"
        anomaly_score = round(evt.anomaly_score, 4) if evt else "—"
        stability_score = round(evt.stability_score, 4) if evt and evt.stability_score else "—"
        network_load = round(evt.network_load, 4) if evt and evt.network_load else "—"
        risk_level = evt.risk_level if evt else "—"

        row_data = [
            session.session_id,
            session.ip_address,
            fmt_time(session.login_time),
            fmt_time(session.logout_time) if session.status == "ENDED" else "— online —",
            fmt_duration(session.login_time, session.logout_time),
            fmt_bytes(session.traffic_bytes),
            destination,
            anomaly_score,
            stability_score,
            network_load,
            risk_level,
        ]

        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(horizontal="left", vertical="center")
            # Alternate row color
            if row_idx % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="161d2e")

        ws.row_dimensions[row_idx].height = 16

    # Save to buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"sessions_{today_str}.xlsx"
    headers_resp = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers_resp,
    )