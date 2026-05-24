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
    24h → TODAY from 00:00 to now, split into 2-hour buckets.
          Labels: "00", "02", "04", ..., up to current hour.
          This gives REAL-TIME data for today only.

    7d  → Last 7 days, one bucket per day.
          Labels: "Mon", "Tue", ...
    """
    now = datetime.utcnow()

    if period == "24h":
        # Start from today 00:00, end at now
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Build 2-hour buckets from 00:00 to now
        labels, unique_ips, blocked_counts = [], [], []

        hour = 0
        while hour < 24:
            b_start = today_start + timedelta(hours=hour)
            b_end   = b_start + timedelta(hours=2)

            # Don't go past current time
            if b_start > now:
                break

            # Cap bucket end at now for the current bucket
            actual_end = min(b_end, now)

            ip_count = (
                db.query(func.count(func.distinct(models.Event.source_ip)))
                .filter(
                    models.Event.timestamp >= b_start,
                    models.Event.timestamp < actual_end,
                )
                .scalar() or 0
            )
            block_count = (
                db.query(func.count(models.Event.id))
                .filter(
                    models.Event.timestamp >= b_start,
                    models.Event.timestamp < actual_end,
                    models.Event.action_taken == "TEMP_BLOCK",
                )
                .scalar() or 0
            )

            labels.append(f"{hour:02d}")
            unique_ips.append(ip_count)
            blocked_counts.append(block_count)

            hour += 2

    else:  # 7d
        labels, unique_ips, blocked_counts = [], [], []
        start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(7):
            b_start = start + timedelta(days=i)
            b_end   = b_start + timedelta(days=1)

            ip_count = (
                db.query(func.count(func.distinct(models.Event.source_ip)))
                .filter(
                    models.Event.timestamp >= b_start,
                    models.Event.timestamp < b_end,
                )
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

            labels.append(b_start.strftime("%a"))
            unique_ips.append(ip_count)
            blocked_counts.append(block_count)

    return {"labels": labels, "unique_ips": unique_ips, "blocked_ips": blocked_counts}