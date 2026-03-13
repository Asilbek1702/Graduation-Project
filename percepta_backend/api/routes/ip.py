"""IP status route: GET /api/ip/{ip_address}"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api import crud, schemas

router = APIRouter(prefix="/api/ip", tags=["IP Status"])


@router.get("/{ip_address}", response_model=schemas.IPStatusResponse)
def get_ip_status(ip_address: str, db: Session = Depends(get_db)):
    """
    Check the current block status for a specific IP address.
    Returns is_blocked, block expiry, strike count, and risk level.
    """
    return crud.get_ip_status(db, ip_address)
