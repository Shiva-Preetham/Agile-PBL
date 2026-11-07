"""US04: churn probability from the trained XGBoost model."""
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from app.config import MODEL_PATH
from app.services.features import build_feature_matrix
from app.services.fields import FEATURE_NAMES, ID_COLUMN
from app.services.risk import classify_risk
from app.services.validation import validate_dataframe


class InvalidFeaturesError(ValueError):
    """Raised when single-customer input is missing fields or has bad values."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class ChurnPredictor:
    def __init__(self, model_path: Path = MODEL_PATH):
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. Train it first: python -m ml.train"
            )
        self.model = XGBClassifier()
        self.model.load_model(model_path)

    def predict_proba(self, data: pd.DataFrame) -> np.ndarray:
        """Churn probability for every row of *validated* customer data."""
        return self.model.predict_proba(build_feature_matrix(data))[:, 1]

    def predict_one(self, features: dict) -> float:
        """Validate one customer's raw features, then predict."""
        return float(self.predict_proba(validate_features(features))[0])


def validate_features(features: dict) -> pd.DataFrame:
    """Reuse the CSV validator so single predictions follow exactly the same rules."""
    row = {ID_COLUMN: "single-prediction", **{k: v for k, v in features.items() if k in FEATURE_NAMES}}
    result = validate_dataframe(pd.DataFrame([row]))
    if not result.is_valid:
        raise InvalidFeaturesError([_strip_row_prefix(e) for e in result.errors])
    return result.data


def score_customers(data: pd.DataFrame) -> pd.DataFrame:
    """Add churn_probability and risk_category columns to validated data."""
    scored = data.copy()
    probabilities = get_predictor().predict_proba(data)
    scored["churn_probability"] = [float(p) for p in probabilities]
    scored["risk_category"] = [classify_risk(float(p)) for p in probabilities]
    return scored


@lru_cache(maxsize=1)
def get_predictor() -> ChurnPredictor:
    return ChurnPredictor()


def _strip_row_prefix(message: str) -> str:
    return message.split(": ", 1)[1] if message.startswith("Row ") else message
