"""Blocked IP routes: GET /api/blocked, POST /api/unblock/{ip}"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api import crud, schemas

router = APIRouter(prefix="/api", tags=["Blocked IPs"])


@router.get("/blocked", response_model=List[schemas.BlockedIPResponse])
def get_blocked_ips(db: Session = Depends(get_db)):
    """
    Return all currently active blocked IPs.
    Used by the Blocked IPs page in the dashboard.
    """
    return crud.get_blocked_ips(db)


@router.post("/unblock/{ip_address}")
def unblock_ip(ip_address: str, db: Session = Depends(get_db)):
    """
    Admin manually unblocks an IP address.
    Returns 404 if the IP is not currently blocked.
    """
    success = crud.unblock_ip(db, ip_address)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"IP '{ip_address}' is not currently blocked."
        )
    return {"message": f"IP '{ip_address}' has been unblocked successfully."}
