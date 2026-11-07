"""US07: explain each prediction with SHAP.

SHAP gives every feature a *contribution* (in log-odds) so that

    base_value + sum(contributions) = model output for this customer

A positive contribution pushes the customer towards churning; a negative one
keeps them. One-hot columns (e.g. contract_type__Two_year) are added back
together so analysts see the original, readable field.
"""
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd
import shap

from app.services.features import MODEL_COLUMNS, SOURCE_FEATURE, build_feature_matrix
from app.services.fields import FEATURE_NAMES, FIELD_LABELS
from app.services.prediction import get_predictor


@dataclass(frozen=True)
class Factor:
    feature: str
    label: str
    value: object
    contribution: float

    @property
    def effect(self) -> str:
        return "increases risk" if self.contribution > 0 else "reduces risk"


@dataclass(frozen=True)
class Explanation:
    probability: float
    base_value: float
    factors: list[Factor]  # every field, strongest impact first

    def top(self, n: int = 5) -> list[Factor]:
        return self.factors[:n]

    def risk_drivers(self, n: int = 3) -> list[Factor]:
        return [f for f in self.factors if f.contribution > 0][:n]


def explain(data: pd.DataFrame) -> list[Explanation]:
    """One explanation per row of validated customer data."""
    explainer = _explainer()
    shap_values = np.asarray(explainer.shap_values(build_feature_matrix(data)))
    per_field = group_by_field(shap_values)
    base_value = float(np.ravel(explainer.expected_value)[0])
    probabilities = get_predictor().predict_proba(data)

    explanations = []
    for i, record in enumerate(data.to_dict(orient="records")):
        factors = [
            Factor(name, FIELD_LABELS[name], _plain(record[name]), float(per_field[i, j]))
            for j, name in enumerate(FEATURE_NAMES)
        ]
        factors.sort(key=lambda f: abs(f.contribution), reverse=True)
        explanations.append(Explanation(float(probabilities[i]), base_value, factors))
    return explanations


def group_by_field(shap_values: np.ndarray) -> np.ndarray:
    """Sum one-hot SHAP columns back into one value per original customer field."""
    position = {name: j for j, name in enumerate(FEATURE_NAMES)}
    grouped = np.zeros((shap_values.shape[0], len(FEATURE_NAMES)))
    for column_index, column in enumerate(MODEL_COLUMNS):
        grouped[:, position[SOURCE_FEATURE[column]]] += shap_values[:, column_index]
    return grouped


@lru_cache(maxsize=1)
def _explainer() -> shap.TreeExplainer:
    return shap.TreeExplainer(get_predictor().model)


def _plain(value):
    """numpy scalars -> plain Python values (JSON friendly)."""
    return value.item() if isinstance(value, np.generic) else value
