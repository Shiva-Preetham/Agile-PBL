"""Customer endpoints.

US01 upload · US02 search · US03 profile · US07 explanation ·
US08 recommendation · US09 action status
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer
from app.schemas import (
    ActionOut,
    CustomerPage,
    CustomerProfile,
    CustomerSummary,
    ExplanationOut,
    FactorOut,
    RecommendationOut,
    StatusUpdate,
    UploadResult,
)
from app.services import actions as action_service
from app.services import customers as customer_service
from app.services.explain import Explanation, explain
from app.services.prediction import score_customers
from app.services.recommend import recommend
from app.services.validation import validate_csv_bytes

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.post("/upload", response_model=UploadResult)
async def upload_customers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(400, detail={"errors": ["Please upload a .csv file."]})

    result = validate_csv_bytes(await file.read())
    if not result.is_valid:
        raise HTTPException(400, detail={"errors": result.errors})

    scored = score_customers(result.data)
    inserted, updated, customers = customer_service.upsert_customers(db, scored)
    recommendations = [
        recommend(risk, explanation.factors)
        for risk, explanation in zip(scored["risk_category"], explain(result.data))
    ]
    action_service.sync_actions(db, customers, recommendations)

    return UploadResult(
        inserted=inserted, updated=updated, total_customers=customer_service.count_customers(db)
    )


@router.get("", response_model=CustomerPage)
def list_customers(
    search: str | None = None,
    contract_type: str | None = None,
    internet_service: str | None = None,
    risk: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows, total = customer_service.search_customers(
        db, search, contract_type, internet_service, risk, page, page_size
    )
    return CustomerPage(
        items=[CustomerSummary.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{customer_id}", response_model=CustomerProfile)
def get_customer_profile(customer_id: str, db: Session = Depends(get_db)):
    return CustomerProfile.model_validate(_find(db, customer_id))


@router.get("/{customer_id}/explanation", response_model=ExplanationOut)
def get_explanation(customer_id: str, top: int = Query(5, ge=1, le=10), db: Session = Depends(get_db)):
    customer, explanation = _find_and_explain(db, customer_id)
    return ExplanationOut(
        customer_id=customer.customer_id,
        churn_probability=explanation.probability,
        risk_category=customer.risk_category,
        base_value=explanation.base_value,
        factors=[
            FactorOut(feature=f.feature, label=f.label, value=f.value,
                      contribution=round(f.contribution, 4), effect=f.effect)
            for f in explanation.top(top)
        ],
    )


@router.get("/{customer_id}/recommendation", response_model=RecommendationOut)
def get_recommendation(customer_id: str, db: Session = Depends(get_db)):
    customer, explanation = _find_and_explain(db, customer_id)
    suggestion = recommend(customer.risk_category, explanation.factors)
    return RecommendationOut(
        customer_id=customer.customer_id,
        risk_category=customer.risk_category,
        rule_id=suggestion.rule_id,
        action=suggestion.action,
        reason=suggestion.reason,
        requires_human_review=suggestion.requires_human_review,
    )


@router.patch("/{customer_id}/action", response_model=ActionOut)
def update_action_status(customer_id: str, update: StatusUpdate, db: Session = Depends(get_db)):
    customer = _find(db, customer_id)
    if customer.action is None:
        raise HTTPException(404, detail=f"Customer '{customer_id}' has no retention action (Low risk).")
    try:
        action = action_service.update_status(db, customer.action, update.status)
    except action_service.InvalidStatusError as error:
        raise HTTPException(422, detail=str(error))
    except action_service.InvalidTransitionError as error:
        raise HTTPException(409, detail=str(error))
    return ActionOut.model_validate(action)


def _find(db: Session, customer_id: str) -> Customer:
    customer = customer_service.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(404, detail=f"Customer '{customer_id}' was not found.")
    return customer


def _find_and_explain(db: Session, customer_id: str) -> tuple[Customer, Explanation]:
    """Look up a stored customer and explain their current prediction."""
    customer = _find(db, customer_id)
    return customer, explain(customer_service.to_frame(customer))[0]
