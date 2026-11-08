"""Demo data for the hosted version, so the dashboard is never empty.

Runs on start-up only when SEED_DEMO_DATA=true, and only if the database
has no customers yet: real uploads and status changes are never overwritten.
"""
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import DEMO_DATA_PATH
from app.services.customers import count_customers
from app.services.ingest import ingest_customers
from app.services.validation import validate_csv_bytes


def seed_demo_data(db: Session, path: Path = DEMO_DATA_PATH) -> int:
    """Load the sample customers into an empty database. Returns how many were added."""
    if count_customers(db) > 0:
        return 0
    result = validate_csv_bytes(path.read_bytes())
    if not result.is_valid:
        raise ValueError("Demo data failed validation:\n" + "\n".join(result.errors))
    inserted, _ = ingest_customers(db, result.data)
    return inserted
