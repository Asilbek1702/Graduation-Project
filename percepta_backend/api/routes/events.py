"""Event routes: POST /api/events, GET /api/events, GET /api/events/{event_id}"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api import crud, schemas

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.post("/", response_model=schemas.EventResponse, status_code=201)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    Receive a new IDS/IPS event from the ML engine.
    Automatically manages BlockedIP table for TEMP_BLOCK actions.
    """
    # Check for duplicate event_id
    existing = crud.get_event_by_id(db, event.event_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Event '{event.event_id}' already exists.")
    return crud.create_event(db, event)


@router.get("/", response_model=List[schemas.EventResponse])
def get_events(
    limit: int = Query(default=100, le=1000),
    risk_level: Optional[str] = Query(default=None, description="LOW | MEDIUM | HIGH | CRITICAL"),
    source_ip: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Return latest events. Supports filters: limit, risk_level, source_ip.
    Used by the dashboard event table.
    """
    return crud.get_events(db, limit=limit, risk_level=risk_level, source_ip=source_ip)


@router.get("/{event_id}", response_model=schemas.EventResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    """
    Return full details for a single event.
    Used when the admin clicks View on an event row.
    """
    event = crud.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    return event
