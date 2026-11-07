"""US10: portfolio-level risk summary for the dashboard."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer, RetentionAction
from app.services.actions import ACTION_STATUSES
from app.services.fields import CONTRACT_TYPES
from app.services.risk import RISK_CATEGORIES

TOP_N = 5


def summarize(db: Session, contract_type: str | None = None, internet_service: str | None = None) -> dict:
    filters = []
    if contract_type:
        filters.append(Customer.contract_type == contract_type)
    if internet_service:
        filters.append(Customer.internet_service == internet_service)

    risk_counts = dict.fromkeys(RISK_CATEGORIES, 0)
    for category, count in db.execute(
        select(Customer.risk_category, func.count()).where(*filters).group_by(Customer.risk_category)
    ):
        if category in risk_counts:
            risk_counts[category] = count

    status_counts = dict.fromkeys(ACTION_STATUSES, 0)
    for status, count in db.execute(
        select(RetentionAction.status, func.count())
        .join(Customer, RetentionAction.customer_pk == Customer.id)
        .where(*filters)
        .group_by(RetentionAction.status)
    ):
        status_counts[status] = count

    by_contract = {c: dict.fromkeys(RISK_CATEGORIES, 0) for c in CONTRACT_TYPES}
    for contract, category, count in db.execute(
        select(Customer.contract_type, Customer.risk_category, func.count())
        .where(*filters)
        .group_by(Customer.contract_type, Customer.risk_category)
    ):
        if contract in by_contract and category in RISK_CATEGORIES:
            by_contract[contract][category] = count

    average = db.scalar(select(func.avg(Customer.churn_probability)).where(*filters))
    top_customers = db.scalars(
        select(Customer).where(*filters).order_by(Customer.churn_probability.desc().nulls_last()).limit(TOP_N)
    ).all()

    return {
        "total_customers": db.scalar(select(func.count()).select_from(Customer).where(*filters)) or 0,
        "risk_counts": risk_counts,
        "average_churn_probability": None if average is None else round(float(average), 4),
        "action_status_counts": status_counts,
        "risk_by_contract": [{"contract_type": c, **counts} for c, counts in by_contract.items()],
        "top_risk_customers": [
            {
                "customer_id": c.customer_id,
                "churn_probability": c.churn_probability,
                "risk_category": c.risk_category,
                "contract_type": c.contract_type,
            }
            for c in top_customers
        ],
    }
