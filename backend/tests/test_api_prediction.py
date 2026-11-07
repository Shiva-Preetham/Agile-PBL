"""US04-US06 through the REST API."""
from app.services.risk import classify_risk
from tests.conftest import loyal_row, make_row, risky_row, upload


def features(row):
    return {k: v for k, v in row.items() if k != "customer_id"}


# ---------- US04 + US05: probability and risk shown together ----------

def test_upload_assigns_probability_and_matching_risk(client):
    upload(client, [risky_row(), loyal_row(), make_row("CS-MID")])

    for customer_id in ("CS-RISKY", "CS-LOYAL", "CS-MID"):
        profile = client.get(f"/api/customers/{customer_id}").json()
        assert 0.0 <= profile["churn_probability"] <= 1.0
        assert profile["risk_category"] == classify_risk(profile["churn_probability"])


def test_risky_customer_is_high_and_loyal_customer_is_low(client):
    upload(client, [risky_row(), loyal_row()])

    assert client.get("/api/customers/CS-RISKY").json()["risk_category"] == "High"
    assert client.get("/api/customers/CS-LOYAL").json()["risk_category"] == "Low"


def test_customer_list_shows_highest_risk_first(client):
    upload(client, [loyal_row(), make_row("CS-MID"), risky_row()])

    items = client.get("/api/customers").json()["items"]
    probabilities = [c["churn_probability"] for c in items]

    assert probabilities == sorted(probabilities, reverse=True)
    assert items[0]["customer_id"] == "CS-RISKY"


def test_filter_by_risk_category(client):
    upload(client, [risky_row(), loyal_row()])

    body = client.get("/api/customers", params={"risk": "High"}).json()

    assert [c["customer_id"] for c in body["items"]] == ["CS-RISKY"]


def test_predict_endpoint_returns_probability_and_risk(client):
    response = client.post("/api/predict", json=features(make_row()))

    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert body["risk_category"] == classify_risk(body["churn_probability"])


def test_predict_endpoint_rejects_missing_feature(client):
    incomplete = features(make_row())
    del incomplete["tenure_months"]

    response = client.post("/api/predict", json=incomplete)

    assert response.status_code == 422
    assert any("tenure_months" in e for e in response.json()["detail"]["errors"])


# ---------- US06: model evaluation metrics ----------

def test_model_metrics_are_holdout_results(client):
    metrics = client.get("/api/model/metrics").json()

    holdout = metrics["holdout_metrics"]
    for name in ("precision", "recall", "f1", "roc_auc", "accuracy"):
        assert 0.0 <= holdout[name] <= 1.0
    assert metrics["split"]["n_test"] > 0
    assert "holdout" in metrics["split"]["evaluated_on"].lower()


def test_training_metrics_are_labelled_separately(client):
    metrics = client.get("/api/model/metrics").json()

    assert "training_metrics" in metrics
    assert metrics["training_metrics"] is not metrics["holdout_metrics"]
    assert "not" in metrics["training_metrics_note"].lower()


def test_model_has_useful_discrimination(client):
    # Sanity check: clearly better than guessing (ROC-AUC 0.5).
    assert client.get("/api/model/metrics").json()["holdout_metrics"]["roc_auc"] > 0.75
