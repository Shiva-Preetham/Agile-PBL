"""The full pipeline for a batch of validated customers.

Used by the CSV upload endpoint and by demo seeding, so both always behave
the same: score -> store -> explain -> Next Best Action -> follow-up actions.
"""
import pandas as pd
from sqlalchemy.orm import Session

from app.services import actions as action_service
from app.services import customers as customer_service
from app.services.explain import explain
from app.services.next_best_action import next_best_actions
from app.services.prediction import score_customers


def ingest_customers(db: Session, data: pd.DataFrame) -> tuple[int, int]:
    """Store validated customers with predictions and follow-ups. Returns (inserted, updated)."""
    scored = score_customers(data)
    inserted, updated, customers = customer_service.upsert_customers(db, scored)
    plans = next_best_actions(data, explain(data))
    action_service.sync_actions(db, customers, [plan.best for plan in plans])
    return inserted, updated
