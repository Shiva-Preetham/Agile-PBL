"""US05: turn a churn probability into a Low / Medium / High risk category.

Documented thresholds (a boundary value belongs to the higher category):

    Low     0.00 <= p < 0.40
    Medium  0.40 <= p < 0.70
    High    0.70 <= p <= 1.00
"""
import math
import numbers

MEDIUM_THRESHOLD = 0.40
HIGH_THRESHOLD = 0.70
RISK_CATEGORIES = ("Low", "Medium", "High")


def classify_risk(probability) -> str:
    if isinstance(probability, bool) or not isinstance(probability, numbers.Real):
        raise ValueError(f"Churn probability must be a number, got {probability!r}.")
    if math.isnan(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError(f"Churn probability must be between 0 and 1, got {probability}.")

    if probability >= HIGH_THRESHOLD:
        return "High"
    if probability >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Low"
