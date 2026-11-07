"""Customer endpoints: upload (US01), search (US02), profile (US03)."""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CustomerPage, CustomerProfile, CustomerSummary, UploadResult
from app.services import customers as customer_service
from app.services.validation import validate_csv_bytes

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.post("/upload", response_model=UploadResult)
async def upload_customers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(400, detail={"errors": ["Please upload a .csv file."]})

    result = validate_csv_bytes(await file.read())
    if not result.is_valid:
        raise HTTPException(400, detail={"errors": result.errors})

    inserted, updated = customer_service.upsert_customers(db, result.data)
    return UploadResult(
        inserted=inserted, updated=updated, total_customers=customer_service.count_customers(db)
    )


@router.get("", response_model=CustomerPage)
def list_customers(
    search: str | None = None,
    contract_type: str | None = None,
    internet_service: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows, total = customer_service.search_customers(
        db, search, contract_type, internet_service, page, page_size
    )
    return CustomerPage(
        items=[CustomerSummary.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{customer_id}", response_model=CustomerProfile)
def get_customer_profile(customer_id: str, db: Session = Depends(get_db)):
    customer = customer_service.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(404, detail=f"Customer '{customer_id}' was not found.")
    return CustomerProfile.model_validate(customer)
