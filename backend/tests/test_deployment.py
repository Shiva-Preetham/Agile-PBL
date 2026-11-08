"""US15: hosted deployment (Render backend + Vercel frontend).

Acceptance: hosting-provider database URLs work with SQLAlchemy; only the
local dev server and Vercel sites may call the API from a browser; an empty
database is filled with demo customers on start-up, exactly once.
"""
import pytest
from sqlalchemy import func, select

from app.config import normalize_database_url
from app.database import SessionLocal
from app.models import Customer, RetentionAction
from app.seed import seed_demo_data


# ---------- database URL from the hosting provider ----------

@pytest.mark.parametrize(
    "given, expected",
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///churnsense.db", "sqlite:///churnsense.db"),
        ("sqlite://", "sqlite://"),
    ],
)
def test_database_url_is_normalised_for_sqlalchemy(given, expected):
    assert normalize_database_url(given) == expected


# ---------- CORS: which websites may call the API ----------

@pytest.mark.parametrize(
    "origin",
    ["http://localhost:5173", "https://agile-pbl.vercel.app", "https://churnsense-git-main-team.vercel.app"],
)
def test_frontend_origins_are_allowed(client, origin):
    response = client.get("/api/health", headers={"Origin": origin})

    assert response.headers.get("access-control-allow-origin") == origin


@pytest.mark.parametrize("origin", ["https://evil.example.com", "https://vercel.app.evil.com"])
def test_other_origins_are_not_allowed(client, origin):
    response = client.get("/api/health", headers={"Origin": origin})

    assert "access-control-allow-origin" not in response.headers


# ---------- demo data for the hosted demo ----------

def test_empty_database_is_seeded_with_scored_demo_customers(client):
    with SessionLocal() as db:
        inserted = seed_demo_data(db)

        assert inserted == 250
        assert db.scalar(select(func.count()).select_from(Customer)) == 250
        assert db.scalar(select(func.count()).where(Customer.churn_probability.is_(None))) == 0
        assert db.scalar(select(func.count()).select_from(RetentionAction)) > 0


def test_seeding_never_touches_a_database_that_has_data(client):
    with SessionLocal() as db:
        seed_demo_data(db)

        assert seed_demo_data(db) == 0
        assert db.scalar(select(func.count()).select_from(Customer)) == 250


def test_seeded_customers_are_visible_through_the_api(client):
    with SessionLocal() as db:
        seed_demo_data(db)

    summary = client.get("/api/dashboard/summary").json()

    assert summary["total_customers"] == 250
    assert summary["risk_counts"]["High"] > 0
