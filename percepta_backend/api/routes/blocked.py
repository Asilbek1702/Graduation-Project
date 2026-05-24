"""Blocked IP routes: GET /api/blocked, POST /api/unblock/{ip}, POST /api/block/{ip}"""

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api import crud, schemas, models

router = APIRouter(prefix="/api", tags=["Blocked IPs"])


@router.get("/blocked", response_model=List[schemas.BlockedIPResponse])
def get_blocked_ips(db: Session = Depends(get_db)):
    """Return all currently active blocked IPs."""
    return crud.get_blocked_ips(db)


@router.post("/unblock/{ip_address}")
def unblock_ip(ip_address: str, db: Session = Depends(get_db)):
    """Admin manually unblocks an IP address."""
    success = crud.unblock_ip(db, ip_address)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"IP '{ip_address}' is not currently blocked."
        )
    return {"message": f"IP '{ip_address}' has been unblocked successfully."}


@router.post("/block/{ip_address}")
def manual_block_ip(ip_address: str, db: Session = Depends(get_db)):
    """
    Admin manually blocks an IP address for 120 seconds.
    If already blocked, refreshes the block timer.
    """
    now = datetime.utcnow()
    expires = now + timedelta(seconds=120)

    record = db.query(models.BlockedIP).filter(
        models.BlockedIP.ip_address == ip_address
    ).first()

    if record:
        record.strike_count += 1
        record.blocked_at = now
        record.block_expires_at = expires
        record.current_risk_level = "CRITICAL"
        record.is_active = True
        record.reason = "Manually blocked by admin"
    else:
        record = models.BlockedIP(
            ip_address=ip_address,
            blocked_at=now,
            block_expires_at=expires,
            strike_count=1,
            current_risk_level="CRITICAL",
            is_active=True,
            reason="Manually blocked by admin",
        )
        db.add(record)

    db.commit()
    return {"message": f"IP '{ip_address}' has been blocked for 120 seconds."}