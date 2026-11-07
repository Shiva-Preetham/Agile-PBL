"""Train the churn model and record honest holdout metrics (US04, US06).

Usage (from backend/):
    python -m ml.train

Outputs:
    models/churn_model.json   trained XGBoost model
    models/metrics.json       holdout metrics (+ training metrics, clearly labelled)
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import shap
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.config import BACKEND_DIR, METRICS_PATH, MODEL_DIR, MODEL_PATH
from app.services.explain import group_by_field
from app.services.features import build_feature_matrix
from app.services.fields import FEATURE_NAMES, FIELD_LABELS
from app.services.validation import validate_dataframe

DATA_PATH = BACKEND_DIR / "data" / "training_customers.csv"
LABEL = "churn"
TEST_SIZE = 0.2
RANDOM_STATE = 42
DECISION_THRESHOLD = 0.5
MODEL_PARAMS = {
    "n_estimators": 300,
    "max_depth": 3,
    "learning_rate": 0.05,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "random_state": RANDOM_STATE,
    "eval_metric": "logloss",
    "n_jobs": 1,
}


def load_training_data():
    raw = pd.read_csv(DATA_PATH, dtype=str, keep_default_na=False)
    result = validate_dataframe(raw.drop(columns=[LABEL]))
    if not result.is_valid:
        raise ValueError("Training data failed validation:\n" + "\n".join(result.errors))
    return build_feature_matrix(result.data), raw[LABEL].astype(int)


def evaluate(model, features, labels) -> dict:
    probabilities = model.predict_proba(features)[:, 1]
    predictions = (probabilities >= DECISION_THRESHOLD).astype(int)
    return {
        "accuracy": round(accuracy_score(labels, predictions), 4),
        "precision": round(precision_score(labels, predictions), 4),
        "recall": round(recall_score(labels, predictions), 4),
        "f1": round(f1_score(labels, predictions), 4),
        "roc_auc": round(roc_auc_score(labels, probabilities), 4),
    }


def global_importance(model, features) -> list[dict]:
    """Mean |SHAP| per customer field on the holdout set: which fields matter most overall."""
    shap_values = np.asarray(shap.TreeExplainer(model).shap_values(features))
    mean_impact = np.abs(group_by_field(shap_values)).mean(axis=0)
    ranking = sorted(zip(FEATURE_NAMES, mean_impact), key=lambda item: item[1], reverse=True)
    return [
        {"feature": name, "label": FIELD_LABELS[name], "mean_abs_shap": round(float(value), 4)}
        for name, value in ranking
    ]


def train() -> dict:
    features, labels = load_training_data()
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=TEST_SIZE, stratify=labels, random_state=RANDOM_STATE
    )

    model = XGBClassifier(**MODEL_PARAMS)
    model.fit(x_train, y_train)

    holdout_predictions = (model.predict_proba(x_test)[:, 1] >= DECISION_THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, holdout_predictions).ravel()

    metrics = {
        "model": "XGBoost classifier (gradient-boosted decision trees)",
        "params": MODEL_PARAMS,
        "dataset": {
            "name": "Synthetic telecom customers (ml/generate_data.py, seed 42)",
            "rows": int(len(labels)),
            "churn_rate": round(float(labels.mean()), 4),
        },
        "split": {
            "method": "Stratified train/test split",
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE,
            "n_train": int(len(y_train)),
            "n_test": int(len(y_test)),
            "evaluated_on": "Holdout test set (20% of rows, never seen during training)",
        },
        "decision_threshold": DECISION_THRESHOLD,
        "holdout_metrics": evaluate(model, x_test, y_test),
        "holdout_confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "training_metrics": evaluate(model, x_train, y_train),
        "training_metrics_note": "Training-set scores are for overfitting checks only and are NOT holdout results.",
        "global_importance": global_importance(model, x_test),
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    result = train()
    print("Holdout metrics:", result["holdout_metrics"])
    print("Training metrics (overfitting check only):", result["training_metrics"])
    print(f"Saved model to {MODEL_PATH}")
