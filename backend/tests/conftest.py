"""Shared test fixtures and helpers.

Every test runs against a fresh in-memory SQLite database, so tests never
touch the real `churnsense.db` file and never depend on each other.
"""
import csv
import io
import os

# Set before the app is imported. Tests drop and recreate every table, so they
# never use DATABASE_URL (which may point at real data). They use an in-memory
# DB, or TEST_DATABASE_URL (CI sets it to run the suite on PostgreSQL too).
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite://")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

COLUMNS = [
    "customer_id",
    "tenure_months",
    "contract_type",
    "monthly_charges",
    "total_charges",
    "internet_service",
    "tech_support",
    "payment_method",
    "support_tickets",
    "monthly_usage_gb",
    "days_since_last_login",
]


def make_row(customer_id="CS-1001", **overrides):
    """A valid, average customer. Override any field to build edge cases."""
    row = {
        "customer_id": customer_id,
        "tenure_months": "24",
        "contract_type": "One year",
        "monthly_charges": "65.50",
        "total_charges": "1572.00",
        "internet_service": "DSL",
        "tech_support": "Yes",
        "payment_method": "Credit card",
        "support_tickets": "1",
        "monthly_usage_gb": "120.5",
        "days_since_last_login": "3",
    }
    row.update({k: str(v) for k, v in overrides.items()})
    return row


def risky_row(customer_id="CS-RISKY"):
    """A customer with every classic churn signal (used for high-risk tests)."""
    return make_row(
        customer_id,
        tenure_months=1,
        contract_type="Month-to-month",
        monthly_charges=105.0,
        total_charges=105.0,
        internet_service="Fiber optic",
        tech_support="No",
        payment_method="Electronic check",
        support_tickets=9,
        monthly_usage_gb=4.0,
        days_since_last_login=75,
    )


def at_risk_row(customer_id="CS-ATRISK"):
    """A typical at-risk customer (~89% churn) with several fixable problems."""
    return make_row(
        customer_id,
        contract_type="Month-to-month",
        monthly_charges=85.0,
        internet_service="Fiber optic",
        tech_support="No",
        payment_method="Electronic check",
        support_tickets=3,
        days_since_last_login=15,
    )


def loyal_row(customer_id="CS-LOYAL"):
    """A long-term, engaged customer (used for low-risk tests)."""
    return make_row(
        customer_id,
        tenure_months=70,
        contract_type="Two year",
        monthly_charges=45.0,
        total_charges=3150.0,
        internet_service="DSL",
        tech_support="Yes",
        payment_method="Bank transfer",
        support_tickets=0,
        monthly_usage_gb=180.0,
        days_since_last_login=1,
    )


def to_csv_bytes(rows, columns=None):
    columns = columns or COLUMNS
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def upload(client, rows, filename="customers.csv"):
    return client.post(
        "/api/customers/upload",
        files={"file": (filename, to_csv_bytes(rows), "text/csv")},
    )


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
