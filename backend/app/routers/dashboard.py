"""US10: dashboard summary endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard import summarize

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(
    contract_type: str | None = None,
    internet_service: str | None = None,
    db: Session = Depends(get_db),
):
    return summarize(db, contract_type, internet_service)
