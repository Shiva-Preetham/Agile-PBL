"""Model endpoints: ad-hoc prediction (US04/US05) and evaluation metrics (US06)."""
import json
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from app.config import METRICS_PATH
from app.schemas import PredictionResult
from app.services.prediction import InvalidFeaturesError, get_predictor
from app.services.risk import HIGH_THRESHOLD, MEDIUM_THRESHOLD, classify_risk

router = APIRouter(prefix="/api", tags=["model"])

EXAMPLE_CUSTOMER = {
    "tenure_months": 3,
    "contract_type": "Month-to-month",
    "monthly_charges": 95.5,
    "total_charges": 286.5,
    "internet_service": "Fiber optic",
    "tech_support": "No",
    "payment_method": "Electronic check",
    "support_tickets": 4,
    "monthly_usage_gb": 20.0,
    "days_since_last_login": 21,
}


@router.post("/predict", response_model=PredictionResult)
def predict(features: dict[str, Any] = Body(..., examples=[EXAMPLE_CUSTOMER])):
    try:
        probability = get_predictor().predict_one(features)
    except InvalidFeaturesError as error:
        raise HTTPException(422, detail={"errors": error.errors})
    return PredictionResult(churn_probability=probability, risk_category=classify_risk(probability))


@router.get("/model/metrics")
def model_metrics():
    if not METRICS_PATH.exists():
        raise HTTPException(503, detail="Model has not been trained yet. Run: python -m ml.train")
    metrics = json.loads(METRICS_PATH.read_text())
    metrics["risk_thresholds"] = {
        "Low": f"probability < {MEDIUM_THRESHOLD:.2f}",
        "Medium": f"{MEDIUM_THRESHOLD:.2f} <= probability < {HIGH_THRESHOLD:.2f}",
        "High": f"probability >= {HIGH_THRESHOLD:.2f}",
    }
    return metrics
