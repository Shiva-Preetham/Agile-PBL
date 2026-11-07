"""Customer storage and queries (US01 upsert, US02 search, US03 lookup)."""
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer
from app.services.fields import FEATURE_NAMES, ID_COLUMN

PREDICTION_COLUMNS = ["churn_probability", "risk_category"]


def upsert_customers(db: Session, data: pd.DataFrame) -> tuple[int, int]:
    """Insert new customers and update existing ones. Returns (inserted, updated).

    `data` holds validated features plus, when available, prediction columns.
    """
    stored_columns = FEATURE_NAMES + [c for c in PREDICTION_COLUMNS if c in data.columns]
    ids = data[ID_COLUMN].tolist()
    existing = {c.customer_id: c for c in db.scalars(select(Customer).where(Customer.customer_id.in_(ids)))}

    inserted = updated = 0
    for record in data.to_dict(orient="records"):
        customer = existing.get(record[ID_COLUMN])
        if customer is None:
            customer = Customer(customer_id=record[ID_COLUMN])
            db.add(customer)
            inserted += 1
        else:
            updated += 1
        for name in stored_columns:
            setattr(customer, name, record[name])
    db.commit()
    return inserted, updated


def count_customers(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Customer)) or 0


def search_customers(
    db: Session,
    search: str | None = None,
    contract_type: str | None = None,
    internet_service: str | None = None,
    risk: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[Customer], int]:
    query = select(Customer)
    if search:
        query = query.where(Customer.customer_id.ilike(f"%{search.strip()}%"))
    if contract_type:
        query = query.where(Customer.contract_type == contract_type)
    if internet_service:
        query = query.where(Customer.internet_service == internet_service)
    if risk:
        query = query.where(Customer.risk_category == risk)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    highest_risk_first = (Customer.churn_probability.desc().nulls_last(), Customer.customer_id)
    rows = db.scalars(
        query.order_by(*highest_risk_first).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def get_customer(db: Session, customer_id: str) -> Customer | None:
    return db.scalar(select(Customer).where(Customer.customer_id == customer_id))
