"""US12 refactoring (smells #2 and #3): the frontend must not keep its own copy
of the customer fields or the risk thresholds. The API publishes them once."""
from app.services.fields import FEATURE_NAMES
from app.services.risk import HIGH_THRESHOLD, MEDIUM_THRESHOLD


def test_schema_lists_every_field_in_order(client):
    schema = client.get("/api/model/schema").json()

    assert [f["name"] for f in schema["fields"]] == FEATURE_NAMES


def test_category_fields_list_their_options(client):
    fields = {f["name"]: f for f in client.get("/api/model/schema").json()["fields"]}

    assert fields["contract_type"]["kind"] == "category"
    assert fields["contract_type"]["options"] == ["Month-to-month", "One year", "Two year"]


def test_numeric_fields_include_their_limits(client):
    fields = {f["name"]: f for f in client.get("/api/model/schema").json()["fields"]}

    tenure = fields["tenure_months"]
    assert tenure["kind"] == "number"
    assert (tenure["minimum"], tenure["maximum"], tenure["whole_number"]) == (0, 120, True)
    assert tenure["label"] == "Tenure (months)"


def test_schema_publishes_the_risk_thresholds(client):
    thresholds = client.get("/api/model/schema").json()["risk_thresholds"]

    assert thresholds == {"medium": MEDIUM_THRESHOLD, "high": HIGH_THRESHOLD}
