"""US07: main factors behind a churn prediction (SHAP).

Acceptance: SHAP shows the top contributing factors for the selected
customer; the explanation corresponds to that customer and model output.
"""
import math

import pandas as pd
import pytest

from app.services.explain import explain
from app.services.fields import FEATURE_NAMES
from app.services.prediction import get_predictor
from app.services.validation import validate_dataframe
from tests.conftest import loyal_row, make_row, risky_row


def clean(*rows):
    return validate_dataframe(pd.DataFrame(list(rows))).data


def test_one_explanation_per_customer():
    explanations = explain(clean(make_row("A"), risky_row("B"), loyal_row("C")))

    assert len(explanations) == 3


def test_every_customer_field_is_explained_exactly_once():
    explanation = explain(clean(make_row()))[0]

    assert sorted(f.feature for f in explanation.factors) == sorted(FEATURE_NAMES)


def test_factors_are_sorted_by_impact():
    factors = explain(clean(risky_row()))[0].factors
    impacts = [abs(f.contribution) for f in factors]

    assert impacts == sorted(impacts, reverse=True)


def test_contributions_add_up_to_the_model_output():
    explanation = explain(clean(risky_row()))[0]
    log_odds = math.log(explanation.probability / (1 - explanation.probability))

    total = explanation.base_value + sum(f.contribution for f in explanation.factors)

    assert total == pytest.approx(log_odds, abs=1e-3)


def test_explanation_uses_the_same_probability_as_the_prediction():
    data = clean(make_row())

    explanation = explain(data)[0]

    assert explanation.probability == pytest.approx(float(get_predictor().predict_proba(data)[0]))


def test_explanation_is_specific_to_each_customer():
    risky, loyal = explain(clean(risky_row(), loyal_row()))

    assert [f.contribution for f in risky.factors] != [f.contribution for f in loyal.factors]
    assert risky.top(1)[0].contribution > 0  # strongest factor pushes towards churn
    assert loyal.top(1)[0].contribution < 0  # strongest factor keeps the customer


def test_factor_shows_readable_label_and_the_customers_value():
    explanation = explain(clean(risky_row()))[0]
    contract = next(f for f in explanation.factors if f.feature == "contract_type")

    assert contract.label == "Contract type"
    assert contract.value == "Month-to-month"
    assert contract.effect == "increases risk"


def test_risk_drivers_only_contain_factors_that_increase_risk():
    drivers = explain(clean(risky_row()))[0].risk_drivers(3)

    assert 1 <= len(drivers) <= 3
    assert all(f.contribution > 0 for f in drivers)
