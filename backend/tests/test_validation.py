"""US01: upload a customer CSV.

Acceptance: a valid file with required columns is accepted; missing columns
or unreadable rows produce a clear error.
"""
from app.services.validation import REQUIRED_COLUMNS, validate_csv_bytes
from tests.conftest import COLUMNS, make_row, to_csv_bytes


def test_valid_csv_is_accepted():
    content = to_csv_bytes([make_row("CS-1"), make_row("CS-2"), make_row("CS-3")])

    result = validate_csv_bytes(content)

    assert result.is_valid
    assert result.errors == []
    assert len(result.data) == 3


def test_numbers_are_converted_to_numeric_types():
    result = validate_csv_bytes(to_csv_bytes([make_row("CS-1")]))

    row = result.data.iloc[0]
    assert row["tenure_months"] == 24
    assert row["monthly_charges"] == 65.5


def test_extra_columns_are_ignored():
    rows = [dict(make_row("CS-1"), churn="1")]
    content = to_csv_bytes(rows, columns=COLUMNS + ["churn"])

    result = validate_csv_bytes(content)

    assert result.is_valid
    assert list(result.data.columns) == REQUIRED_COLUMNS


def test_column_names_ignore_case_and_spaces():
    content = b" Customer_ID ,TENURE_MONTHS" + to_csv_bytes([make_row()]).split(b"tenure_months", 1)[1]

    result = validate_csv_bytes(content)

    assert result.is_valid, result.errors


def test_missing_required_columns_are_reported_by_name():
    columns = [c for c in COLUMNS if c not in ("tenure_months", "contract_type")]
    content = to_csv_bytes([make_row()], columns=columns)

    result = validate_csv_bytes(content)

    assert not result.is_valid
    assert "Missing required columns" in result.errors[0]
    assert "tenure_months" in result.errors[0]
    assert "contract_type" in result.errors[0]


def test_empty_file_gives_clear_error():
    result = validate_csv_bytes(b"")

    assert not result.is_valid
    assert "empty" in result.errors[0].lower()


def test_header_only_file_gives_clear_error():
    result = validate_csv_bytes(to_csv_bytes([]))

    assert not result.is_valid
    assert "no customer rows" in result.errors[0].lower()


def test_non_numeric_value_reports_row_and_column():
    rows = [make_row("CS-1"), make_row("CS-2", tenure_months="abc")]

    result = validate_csv_bytes(to_csv_bytes(rows))

    assert not result.is_valid
    # Row 3 = line 3 of the file (line 1 is the header).
    assert any("Row 3" in e and "tenure_months" in e for e in result.errors)


def test_out_of_range_value_is_rejected():
    result = validate_csv_bytes(to_csv_bytes([make_row(monthly_charges="-5")]))

    assert not result.is_valid
    assert "monthly_charges" in result.errors[0]


def test_unknown_category_lists_allowed_values():
    result = validate_csv_bytes(to_csv_bytes([make_row(contract_type="Weekly")]))

    assert not result.is_valid
    assert "contract_type" in result.errors[0]
    assert "Month-to-month" in result.errors[0]


def test_missing_value_is_reported():
    result = validate_csv_bytes(to_csv_bytes([make_row(monthly_charges="")]))

    assert not result.is_valid
    assert "missing" in result.errors[0].lower()


def test_duplicate_customer_ids_are_rejected():
    result = validate_csv_bytes(to_csv_bytes([make_row("CS-1"), make_row("CS-1")]))

    assert not result.is_valid
    assert "duplicate" in result.errors[0].lower()
