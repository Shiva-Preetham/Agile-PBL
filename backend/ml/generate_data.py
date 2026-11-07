"""Generate a realistic *synthetic* telecom customer dataset.

Why synthetic? It keeps the prototype free of private data and fully
reproducible (fixed random seed). The churn label is produced from known,
documented business signals, so we can check that the model and SHAP
discover sensible reasons. The real IBM Telco churn dataset can replace it
later without code changes.

Usage (from backend/):
    python -m ml.generate_data
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def generate(n: int, seed: int, id_prefix: str, id_start: int, with_label: bool) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    contract = rng.choice(["Month-to-month", "One year", "Two year"], n, p=[0.55, 0.25, 0.20])
    max_tenure = np.select([contract == "Month-to-month", contract == "One year"], [36, 60], 72)
    tenure = np.floor(rng.beta(1.1, 1.6, n) * (max_tenure + 1)).astype(int)

    internet = rng.choice(["DSL", "Fiber optic", "No"], n, p=[0.35, 0.45, 0.20])
    base_charge = np.select([internet == "Fiber optic", internet == "DSL"], [88.0, 58.0], 22.0)
    monthly = np.clip(base_charge + rng.normal(0, 9, n), 18, 120).round(2)
    total = (monthly * np.maximum(tenure, 1) * rng.uniform(0.96, 1.04, n)).round(2)

    tech_support = np.where(
        internet == "No", "No", rng.choice(["Yes", "No"], n, p=[0.38, 0.62])
    )
    payment = rng.choice(
        ["Electronic check", "Mailed check", "Bank transfer", "Credit card"], n, p=[0.34, 0.20, 0.23, 0.23]
    )

    engagement = rng.normal(0, 1, n)  # hidden "how much they like the service"
    tickets = np.clip(rng.poisson(1.0 + 1.2 * (internet == "Fiber optic") + 0.8 * (engagement < -0.8)), 0, 15)
    usage = np.where(
        internet == "No", 0.0, np.clip(rng.gamma(2.0, 45, n) * np.exp(0.35 * engagement), 0, 900)
    ).round(1)
    last_login = np.clip(rng.exponential(6 * np.exp(-0.6 * engagement)), 0, 180).astype(int)

    frame = pd.DataFrame({
        "customer_id": [f"{id_prefix}-{id_start + i}" for i in range(n)],
        "tenure_months": tenure,
        "contract_type": contract,
        "monthly_charges": monthly,
        "total_charges": total,
        "internet_service": internet,
        "tech_support": tech_support,
        "payment_method": payment,
        "support_tickets": tickets,
        "monthly_usage_gb": usage,
        "days_since_last_login": last_login,
    })

    if with_label:
        logit = (
            -2.45
            + 1.35 * (contract == "Month-to-month")
            - 0.85 * (contract == "Two year")
            - 0.045 * tenure
            + 0.022 * (monthly - 65)
            + 0.45 * (internet == "Fiber optic")
            + 0.55 * ((tech_support == "No") & (internet != "No"))
            + 0.50 * (payment == "Electronic check")
            + 0.30 * tickets
            + 0.035 * last_login
            - 0.6 * engagement
        )
        probability = 1 / (1 + np.exp(-logit))
        frame["churn"] = (rng.random(n) < probability).astype(int)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--train-rows", type=int, default=3000)
    parser.add_argument("--sample-rows", type=int, default=250)
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    training = generate(args.train_rows, seed=42, id_prefix="TR", id_start=100001, with_label=True)
    training.to_csv(DATA_DIR / "training_customers.csv", index=False)

    sample = generate(args.sample_rows, seed=7, id_prefix="CS", id_start=10001, with_label=False)
    sample.to_csv(DATA_DIR / "sample_customers.csv", index=False)

    print(f"training_customers.csv: {len(training)} rows, churn rate {training['churn'].mean():.1%}")
    print(f"sample_customers.csv:   {len(sample)} rows (no label, for uploading in the app)")


if __name__ == "__main__":
    main()
