"""Stats route: GET /api/stats, GET /api/stats/chart-data"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.database import get_db
from api import crud, schemas, models

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("/", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    return crud.get_stats(db)


@router.get("/chart-data")
def get_chart_data(
    period: str = Query("24h", regex="^(24h|7d)$"),
    db: Session = Depends(get_db),
):
    """
    24h → 12 buckets x 2 hours, labels: "00","02","04",...,"22"
    7d  → 7 buckets x 1 day,   labels: "Mon","Tue",...
    """
    now = datetime.utcnow()

    if period == "24h":
        buckets = 12
        delta   = timedelta(hours=2)
        start   = now - timedelta(hours=24)
        start   = start.replace(minute=0, second=0, microsecond=0)
        if start.hour % 2 != 0:
            start = start - timedelta(hours=1)
    else:
        buckets = 7
        delta   = timedelta(days=1)
        start   = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

    labels, unique_ips, blocked_counts = [], [], []

    for i in range(buckets):
        b_start = start + i * delta
        b_end   = b_start + delta

        ip_count = (
            db.query(func.count(func.distinct(models.Event.source_ip)))
            .filter(models.Event.timestamp >= b_start, models.Event.timestamp < b_end)
            .scalar() or 0
        )
        block_count = (
            db.query(func.count(models.Event.id))
            .filter(
                models.Event.timestamp >= b_start,
                models.Event.timestamp < b_end,
                models.Event.action_taken == "TEMP_BLOCK",
            )
            .scalar() or 0
        )

        labels.append(f"{b_start.hour:02d}" if period == "24h" else b_start.strftime("%a"))
        unique_ips.append(ip_count)
        blocked_counts.append(block_count)

    return {"labels": labels, "unique_ips": unique_ips, "blocked_ips": blocked_counts}