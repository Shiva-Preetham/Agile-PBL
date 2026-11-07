"""Single source of truth for customer fields.

Validation, the ML feature pipeline and the UI labels all read from this
module, so a field is defined in exactly one place.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class NumericField:
    name: str
    label: str
    minimum: float
    maximum: float
    whole_number: bool = False


@dataclass(frozen=True)
class CategoryField:
    name: str
    label: str
    allowed: tuple[str, ...]


CONTRACT_TYPES = ("Month-to-month", "One year", "Two year")
INTERNET_SERVICES = ("DSL", "Fiber optic", "No")
YES_NO = ("Yes", "No")
PAYMENT_METHODS = ("Electronic check", "Mailed check", "Bank transfer", "Credit card")

FEATURE_FIELDS: tuple[NumericField | CategoryField, ...] = (
    NumericField("tenure_months", "Tenure (months)", 0, 120, whole_number=True),
    CategoryField("contract_type", "Contract type", CONTRACT_TYPES),
    NumericField("monthly_charges", "Monthly charges", 0, 1000),
    NumericField("total_charges", "Total charges", 0, 200000),
    CategoryField("internet_service", "Internet service", INTERNET_SERVICES),
    CategoryField("tech_support", "Tech support", YES_NO),
    CategoryField("payment_method", "Payment method", PAYMENT_METHODS),
    NumericField("support_tickets", "Support tickets", 0, 100, whole_number=True),
    NumericField("monthly_usage_gb", "Monthly usage (GB)", 0, 10000),
    NumericField("days_since_last_login", "Days since last login", 0, 3650, whole_number=True),
)

ID_COLUMN = "customer_id"
FEATURE_NAMES = [field.name for field in FEATURE_FIELDS]
FIELD_LABELS = {field.name: field.label for field in FEATURE_FIELDS}
