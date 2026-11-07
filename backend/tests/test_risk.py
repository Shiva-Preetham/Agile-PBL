"""US05: Low / Medium / High risk category.

Acceptance: documented thresholds classify scores consistently; boundary
values map to exactly one category.
Documented thresholds: Low < 0.40 <= Medium < 0.70 <= High
"""
import math

import pytest

from app.services.risk import HIGH_THRESHOLD, MEDIUM_THRESHOLD, RISK_CATEGORIES, classify_risk


def test_thresholds_are_the_documented_values():
    assert MEDIUM_THRESHOLD == 0.40
    assert HIGH_THRESHOLD == 0.70
    assert RISK_CATEGORIES == ("Low", "Medium", "High")


@pytest.mark.parametrize(
    "probability, expected",
    [
        (0.0, "Low"),
        (0.25, "Low"),
        (0.3999, "Low"),
        (0.40, "Medium"),  # boundary belongs to the higher category
        (0.55, "Medium"),
        (0.6999, "Medium"),
        (0.70, "High"),  # boundary belongs to the higher category
        (0.95, "High"),
        (1.0, "High"),
    ],
)
def test_probability_maps_to_expected_category(probability, expected):
    assert classify_risk(probability) == expected


def test_every_probability_maps_to_exactly_one_category():
    for step in range(0, 1001):
        assert classify_risk(step / 1000) in RISK_CATEGORIES


@pytest.mark.parametrize("bad_value", [-0.01, 1.01, math.nan, None, "high"])
def test_invalid_probability_is_rejected(bad_value):
    with pytest.raises(ValueError):
        classify_risk(bad_value)
