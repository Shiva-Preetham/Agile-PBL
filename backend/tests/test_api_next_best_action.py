"""US14 through the REST API."""
from tests.conftest import at_risk_row, loyal_row, upload


def test_next_best_action_endpoint_ranks_options(client):
    upload(client, [at_risk_row()])

    response = client.get("/api/customers/CS-ATRISK/next-best-action")

    assert response.status_code == 200
    body = response.json()
    assert body["best"]["rule_id"] == body["options"][0]["rule_id"]
    assert body["best"]["requires_human_review"] is True
    for option in body["options"]:
        assert option["new_probability"] < body["current_probability"]
        assert {"action", "cost", "change_text", "new_risk", "reduction"} <= set(option)
    assert body["plan"], "an at-risk customer should get a retention plan"
    assert "what-if" in body["note"].lower()


def test_low_risk_customer_has_no_next_best_action(client):
    upload(client, [loyal_row()])

    body = client.get("/api/customers/CS-LOYAL/next-best-action").json()

    assert body["best"]["rule_id"] == "LOW_RISK"
    assert body["options"] == []
    assert body["plan"] == []


def test_unknown_customer_is_not_found(client):
    assert client.get("/api/customers/NOPE/next-best-action").status_code == 404


def test_tracked_follow_up_uses_the_next_best_action(client):
    upload(client, [at_risk_row()])

    nba = client.get("/api/customers/CS-ATRISK/next-best-action").json()
    profile = client.get("/api/customers/CS-ATRISK").json()

    assert profile["action"]["rule_id"] == nba["best"]["rule_id"]


def test_recommendation_endpoint_agrees_with_next_best_action(client):
    upload(client, [at_risk_row()])

    nba = client.get("/api/customers/CS-ATRISK/next-best-action").json()
    recommendation = client.get("/api/customers/CS-ATRISK/recommendation").json()

    assert recommendation["rule_id"] == nba["best"]["rule_id"]
