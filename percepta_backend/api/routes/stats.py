"""Stats route: GET /api/stats — dashboard overview cards."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api import crud, schemas

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("/", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """
    Return system-wide statistics for the dashboard overview.
    Includes: total flows, anomalies, risk distribution, blocked IPs, network load.
    """
    return crud.get_stats(db)
