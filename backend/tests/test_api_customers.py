"""US01-US03 through the REST API: upload, search/filter and customer profile."""
from tests.conftest import make_row, upload


def test_health_check(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ---------- US01: upload ----------

def test_upload_valid_csv_stores_customers(client):
    response = upload(client, [make_row("CS-1"), make_row("CS-2"), make_row("CS-3")])

    assert response.status_code == 200
    assert response.json() == {"inserted": 3, "updated": 0, "total_customers": 3}


def test_upload_invalid_csv_returns_clear_errors(client):
    response = upload(client, [make_row("CS-1", tenure_months="abc")])

    assert response.status_code == 400
    errors = response.json()["detail"]["errors"]
    assert any("tenure_months" in e for e in errors)


def test_upload_rejects_non_csv_file(client):
    response = upload(client, [make_row()], filename="customers.xlsx")

    assert response.status_code == 400
    assert ".csv" in response.json()["detail"]["errors"][0]


def test_reupload_updates_existing_customers(client):
    upload(client, [make_row("CS-1"), make_row("CS-2")])

    response = upload(client, [make_row("CS-1", tenure_months=30), make_row("CS-3")])

    assert response.json() == {"inserted": 1, "updated": 1, "total_customers": 3}
    assert client.get("/api/customers/CS-1").json()["tenure_months"] == 30


# ---------- US02: search & filter ----------

def test_search_by_customer_id(client):
    upload(client, [make_row("CS-ALPHA"), make_row("CS-BETA")])

    body = client.get("/api/customers", params={"search": "alp"}).json()

    assert body["total"] == 1
    assert body["items"][0]["customer_id"] == "CS-ALPHA"


def test_filter_by_contract_type(client):
    upload(client, [
        make_row("CS-1", contract_type="Month-to-month"),
        make_row("CS-2", contract_type="Two year"),
        make_row("CS-3", contract_type="Two year"),
    ])

    body = client.get("/api/customers", params={"contract_type": "Two year"}).json()

    assert body["total"] == 2
    assert {c["customer_id"] for c in body["items"]} == {"CS-2", "CS-3"}


def test_search_with_no_matches_returns_empty_list(client):
    upload(client, [make_row("CS-1")])

    body = client.get("/api/customers", params={"search": "does-not-exist"}).json()

    assert body["total"] == 0
    assert body["items"] == []


def test_list_is_paginated(client):
    upload(client, [make_row(f"CS-{i:02d}") for i in range(15)])

    body = client.get("/api/customers", params={"page": 2, "page_size": 10}).json()

    assert body["total"] == 15
    assert len(body["items"]) == 5


# ---------- US03: customer profile ----------

def test_profile_shows_attributes_and_usage_metrics(client):
    upload(client, [make_row("CS-7", support_tickets=4, monthly_usage_gb=88.5)])

    response = client.get("/api/customers/CS-7")

    assert response.status_code == 200
    profile = response.json()
    assert profile["customer_id"] == "CS-7"
    assert profile["contract_type"] == "One year"
    assert profile["support_tickets"] == 4
    assert profile["monthly_usage_gb"] == 88.5


def test_unknown_customer_returns_not_found(client):
    response = client.get("/api/customers/NOPE-404")

    assert response.status_code == 404
    assert "NOPE-404" in response.json()["detail"]
