"""API response models (what the frontend receives)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadResult(BaseModel):
    inserted: int
    updated: int
    total_customers: int


class ActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    action: str
    status: str
    updated_at: datetime | None = None


class CustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    tenure_months: int
    contract_type: str
    monthly_charges: float
    internet_service: str
    churn_probability: float | None = None
    risk_category: str | None = None


class CustomerProfile(CustomerSummary):
    total_charges: float
    tech_support: str
    payment_method: str
    support_tickets: int
    monthly_usage_gb: float
    days_since_last_login: int
    action: ActionOut | None = None


class CustomerPage(BaseModel):
    items: list[CustomerSummary]
    total: int
    page: int
    page_size: int


class PredictionResult(BaseModel):
    churn_probability: float
    risk_category: str


class FactorOut(BaseModel):
    feature: str
    label: str
    value: str | int | float
    contribution: float
    effect: str


class ExplanationOut(BaseModel):
    customer_id: str
    churn_probability: float
    risk_category: str
    base_value: float
    factors: list[FactorOut]
    note: str = (
        "Contributions are SHAP values in log-odds. Positive values push the customer "
        "towards churn; negative values keep them."
    )


class RecommendationOut(BaseModel):
    customer_id: str
    risk_category: str
    rule_id: str
    action: str
    reason: str
    requires_human_review: bool


class StatusUpdate(BaseModel):
    status: str
