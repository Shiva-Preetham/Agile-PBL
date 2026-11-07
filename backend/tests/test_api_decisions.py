"""US07-US10 through the REST API: explanation, recommendation, action
tracking and the dashboard summary."""
import pytest

from tests.conftest import loyal_row, make_row, risky_row, upload


# ---------- US07: explanation ----------

def test_explanation_endpoint_returns_top_factors(client):
    upload(client, [risky_row()])

    body = client.get("/api/customers/CS-RISKY/explanation").json()

    assert body["customer_id"] == "CS-RISKY"
    assert len(body["factors"]) == 5
    assert {"feature", "label", "value", "contribution", "effect"} <= set(body["factors"][0])


def test_explanation_matches_the_stored_prediction(client):
    upload(client, [risky_row()])
    profile = client.get("/api/customers/CS-RISKY").json()

    body = client.get("/api/customers/CS-RISKY/explanation").json()

    assert body["churn_probability"] == pytest.approx(profile["churn_probability"], abs=1e-6)


def test_explanation_for_unknown_customer_is_not_found(client):
    assert client.get("/api/customers/NOPE/explanation").status_code == 404


# ---------- US08: recommendation ----------

def test_recommendation_is_marked_for_human_review(client):
    upload(client, [risky_row()])

    body = client.get("/api/customers/CS-RISKY/recommendation").json()

    assert body["requires_human_review"] is True
    assert body["action"]
    assert body["rule_id"]


def test_low_risk_customer_gets_low_risk_recommendation(client):
    upload(client, [loyal_row()])

    assert client.get("/api/customers/CS-LOYAL/recommendation").json()["rule_id"] == "LOW_RISK"


# ---------- US09: retention-action status ----------

def test_upload_creates_pending_action_for_at_risk_customers_only(client):
    upload(client, [risky_row(), loyal_row()])

    assert client.get("/api/customers/CS-RISKY").json()["action"]["status"] == "Pending"
    assert client.get("/api/customers/CS-LOYAL").json()["action"] is None


def test_status_update_persists(client):
    upload(client, [risky_row()])

    response = client.patch("/api/customers/CS-RISKY/action", json={"status": "Contacted"})

    assert response.status_code == 200
    assert client.get("/api/customers/CS-RISKY").json()["action"]["status"] == "Contacted"


def test_status_survives_a_reupload(client):
    upload(client, [risky_row()])
    client.patch("/api/customers/CS-RISKY/action", json={"status": "Contacted"})

    upload(client, [risky_row()])

    assert client.get("/api/customers/CS-RISKY").json()["action"]["status"] == "Contacted"


def test_invalid_status_value_is_rejected(client):
    upload(client, [risky_row()])

    response = client.patch("/api/customers/CS-RISKY/action", json={"status": "Done"})

    assert response.status_code == 422
    assert "Pending" in response.json()["detail"]


def test_disallowed_transition_is_rejected(client):
    upload(client, [risky_row()])

    response = client.patch("/api/customers/CS-RISKY/action", json={"status": "Completed"})

    assert response.status_code == 409


def test_customer_without_action_cannot_be_updated(client):
    upload(client, [loyal_row()])

    response = client.patch("/api/customers/CS-LOYAL/action", json={"status": "Contacted"})

    assert response.status_code == 404


# ---------- US10: dashboard ----------

def test_dashboard_counts_match_stored_records(client):
    upload(client, [risky_row(), loyal_row(), make_row("CS-MID")])

    summary = client.get("/api/dashboard/summary").json()

    assert summary["total_customers"] == 3
    assert sum(summary["risk_counts"].values()) == 3
    assert summary["risk_counts"]["High"] >= 1
    assert summary["risk_counts"]["Low"] >= 1
    assert 0.0 <= summary["average_churn_probability"] <= 1.0
    assert summary["top_risk_customers"][0]["customer_id"] == "CS-RISKY"


def test_dashboard_filter_updates_results(client):
    upload(client, [risky_row(), loyal_row()])  # Month-to-month vs Two year

    summary = client.get("/api/dashboard/summary", params={"contract_type": "Two year"}).json()

    assert summary["total_customers"] == 1
    assert summary["risk_counts"]["High"] == 0


def test_dashboard_counts_action_statuses(client):
    upload(client, [risky_row()])
    client.patch("/api/customers/CS-RISKY/action", json={"status": "Contacted"})

    summary = client.get("/api/dashboard/summary").json()

    assert summary["action_status_counts"] == {"Pending": 0, "Contacted": 1, "Completed": 0}


def test_empty_dashboard_does_not_break(client):
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    summary = response.json()
    assert summary["total_customers"] == 0
    assert summary["risk_counts"] == {"Low": 0, "Medium": 0, "High": 0}
    assert summary["average_churn_probability"] is None
    assert summary["top_risk_customers"] == []
