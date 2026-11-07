"""US04: churn probability for a customer.

Acceptance: valid inputs return a probability from 0 to 1; missing/invalid
features are handled clearly; same model + same input = same output.
"""
import pandas as pd
import pytest

from app.services.prediction import InvalidFeaturesError, get_predictor
from app.services.risk import HIGH_THRESHOLD, MEDIUM_THRESHOLD
from app.services.validation import validate_dataframe
from tests.conftest import loyal_row, make_row, risky_row


def features(row):
    return {k: v for k, v in row.items() if k != "customer_id"}


def test_probability_is_between_0_and_1():
    probability = get_predictor().predict_one(features(make_row()))

    assert 0.0 <= probability <= 1.0


def test_same_input_gives_same_output():
    predictor = get_predictor()
    first = predictor.predict_one(features(make_row()))
    second = predictor.predict_one(features(make_row()))

    assert first == second


def test_missing_feature_raises_clear_error():
    incomplete = features(make_row())
    del incomplete["tenure_months"]

    with pytest.raises(InvalidFeaturesError) as error:
        get_predictor().predict_one(incomplete)

    assert "tenure_months" in str(error.value)


def test_invalid_feature_value_raises_clear_error():
    with pytest.raises(InvalidFeaturesError) as error:
        get_predictor().predict_one(features(make_row(contract_type="Weekly")))

    assert "contract_type" in str(error.value)


def test_risky_customer_scores_higher_than_loyal_customer():
    predictor = get_predictor()
    risky = predictor.predict_one(features(risky_row()))
    loyal = predictor.predict_one(features(loyal_row()))

    assert risky >= HIGH_THRESHOLD
    assert loyal < MEDIUM_THRESHOLD


def test_batch_prediction_matches_single_prediction():
    rows = [make_row("A"), risky_row("B"), loyal_row("C")]
    clean = validate_dataframe(pd.DataFrame(rows)).data
    predictor = get_predictor()

    batch = predictor.predict_proba(clean)

    for row, probability in zip(rows, batch):
        assert probability == pytest.approx(predictor.predict_one(features(row)))
