"""US10: portfolio-level risk summary for the dashboard."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer, RetentionAction
from app.services.actions import ACTION_STATUSES
from app.services.fields import CONTRACT_TYPES
from app.services.risk import RISK_CATEGORIES

TOP_N = 5


def summarize(db: Session, contract_type: str | None = None, internet_service: str | None = None) -> dict:
    filters = _filters(contract_type, internet_service)
    return {
        "total_customers": _total(db, filters),
        "risk_counts": _risk_counts(db, filters),
        "average_churn_probability": _average_probability(db, filters),
        "action_status_counts": _action_status_counts(db, filters),
        "risk_by_contract": _risk_by_contract(db, filters),
        "top_risk_customers": _top_risk_customers(db, filters),
    }


def _filters(contract_type: str | None, internet_service: str | None) -> list:
    filters = []
    if contract_type:
        filters.append(Customer.contract_type == contract_type)
    if internet_service:
        filters.append(Customer.internet_service == internet_service)
    return filters


def _total(db: Session, filters: list) -> int:
    return db.scalar(select(func.count()).select_from(Customer).where(*filters)) or 0


def _risk_counts(db: Session, filters: list) -> dict:
    counts = dict.fromkeys(RISK_CATEGORIES, 0)
    query = select(Customer.risk_category, func.count()).where(*filters).group_by(Customer.risk_category)
    for category, count in db.execute(query):
        if category in counts:
            counts[category] = count
    return counts


def _average_probability(db: Session, filters: list) -> float | None:
    average = db.scalar(select(func.avg(Customer.churn_probability)).where(*filters))
    return None if average is None else round(float(average), 4)


def _action_status_counts(db: Session, filters: list) -> dict:
    counts = dict.fromkeys(ACTION_STATUSES, 0)
    query = (
        select(RetentionAction.status, func.count())
        .join(Customer, RetentionAction.customer_pk == Customer.id)
        .where(*filters)
        .group_by(RetentionAction.status)
    )
    for status, count in db.execute(query):
        counts[status] = count
    return counts


def _risk_by_contract(db: Session, filters: list) -> list[dict]:
    table = {contract: dict.fromkeys(RISK_CATEGORIES, 0) for contract in CONTRACT_TYPES}
    query = (
        select(Customer.contract_type, Customer.risk_category, func.count())
        .where(*filters)
        .group_by(Customer.contract_type, Customer.risk_category)
    )
    for contract, category, count in db.execute(query):
        if contract in table and category in RISK_CATEGORIES:
            table[contract][category] = count
    return [{"contract_type": contract, **counts} for contract, counts in table.items()]


def _top_risk_customers(db: Session, filters: list) -> list[dict]:
    customers = db.scalars(
        select(Customer).where(*filters).order_by(Customer.churn_probability.desc().nulls_last()).limit(TOP_N)
    ).all()
    return [
        {
            "customer_id": c.customer_id,
            "churn_probability": c.churn_probability,
            "risk_category": c.risk_category,
            "contract_type": c.contract_type,
        }
        for c in customers
    ]
