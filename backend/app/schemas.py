"""API response models (what the frontend receives)."""
from pydantic import BaseModel, ConfigDict


class UploadResult(BaseModel):
    inserted: int
    updated: int
    total_customers: int


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


class CustomerPage(BaseModel):
    items: list[CustomerSummary]
    total: int
    page: int
    page_size: int


class PredictionResult(BaseModel):
    churn_probability: float
    risk_category: str
