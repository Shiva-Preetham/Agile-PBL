"""US01: validate an uploaded customer CSV before anything is stored.

Every problem is reported with its row number and column, so an analyst can
fix the file without guessing.
"""
import io
from dataclasses import dataclass, field

import pandas as pd

from app.config import MAX_REPORTED_ERRORS
from app.services.fields import FEATURE_FIELDS, ID_COLUMN, CategoryField, NumericField

REQUIRED_COLUMNS = [ID_COLUMN] + [f.name for f in FEATURE_FIELDS]
HEADER_LINES = 1  # data row i is on line i + 2 of the file


@dataclass
class ValidationResult:
    data: pd.DataFrame | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_csv_bytes(content: bytes) -> ValidationResult:
    """Parse and validate raw CSV bytes."""
    if not content or not content.strip():
        return ValidationResult(errors=["The file is empty. Please upload a CSV with customer rows."])
    try:
        frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
        return ValidationResult(errors=[f"The file could not be read as CSV ({exc.__class__.__name__})."])
    return validate_dataframe(frame)


def validate_dataframe(frame: pd.DataFrame) -> ValidationResult:
    """Validate a table of raw (string) values and return typed, clean data."""
    frame = frame.rename(columns=_normalise_column_name)

    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        return ValidationResult(errors=[f"Missing required columns: {', '.join(missing)}."])
    if frame.empty:
        return ValidationResult(errors=["The file has a header but no customer rows."])

    frame = frame[REQUIRED_COLUMNS]
    clean_rows, errors = [], []
    seen_ids: set[str] = set()

    for index, raw in enumerate(frame.to_dict(orient="records")):
        line = index + HEADER_LINES + 1
        row_errors, clean = _validate_row(raw, line, seen_ids)
        errors.extend(row_errors)
        clean_rows.append(clean)

    if errors:
        return ValidationResult(errors=_limit(errors))
    return ValidationResult(data=pd.DataFrame(clean_rows, columns=REQUIRED_COLUMNS))


def _validate_row(raw: dict, line: int, seen_ids: set[str]) -> tuple[list[str], dict]:
    errors: list[str] = []
    clean: dict = {}

    customer_id = str(raw[ID_COLUMN]).strip()
    if not customer_id:
        errors.append(f"Row {line}: '{ID_COLUMN}' is missing.")
    elif customer_id in seen_ids:
        errors.append(f"Row {line}: duplicate {ID_COLUMN} '{customer_id}'.")
    seen_ids.add(customer_id)
    clean[ID_COLUMN] = customer_id

    for spec in FEATURE_FIELDS:
        value = str(raw[spec.name]).strip()
        if value == "":
            errors.append(f"Row {line}: '{spec.name}' is missing.")
            continue
        parsed, message = _parse_value(spec, value)
        if message:
            errors.append(f"Row {line}: '{spec.name}' {message}")
        clean[spec.name] = parsed
    return errors, clean


def _parse_value(spec, value: str):
    """Return (parsed_value, error_message_or_None) for one cell."""
    if isinstance(spec, CategoryField):
        match = next((a for a in spec.allowed if a.lower() == value.lower()), None)
        if match is None:
            return None, f"must be one of {', '.join(spec.allowed)} (got '{value}')."
        return match, None

    assert isinstance(spec, NumericField)
    kind = "a whole number" if spec.whole_number else "a number"
    try:
        number = float(value)
    except ValueError:
        return None, f"must be {kind} (got '{value}')."
    if spec.whole_number and not number.is_integer():
        return None, f"must be {kind} (got '{value}')."
    if not spec.minimum <= number <= spec.maximum:
        return None, f"must be between {spec.minimum:g} and {spec.maximum:g} (got '{value}')."
    return (int(number) if spec.whole_number else number), None


def _normalise_column_name(name: str) -> str:
    return str(name).strip().lower().replace(" ", "_")


def _limit(errors: list[str]) -> list[str]:
    if len(errors) <= MAX_REPORTED_ERRORS:
        return errors
    hidden = len(errors) - MAX_REPORTED_ERRORS
    return errors[:MAX_REPORTED_ERRORS] + [f"…and {hidden} more problem(s)."]
