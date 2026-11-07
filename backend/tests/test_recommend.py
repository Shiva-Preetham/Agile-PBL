"""US08: suggested retention action.

Acceptance: a documented rule returns an action based on risk/factors or a
safe fallback; suggestions are marked for human review.
"""
import pytest

from app.services.explain import Factor
from app.services.recommend import FALLBACK, LOW_RISK, RULES, recommend


def factor(feature, contribution, value="x"):
    return Factor(feature=feature, label=feature, value=value, contribution=contribution)


def test_low_risk_customer_needs_no_immediate_action():
    result = recommend("Low", [factor("contract_type", 0.8)])

    assert result.rule_id == LOW_RISK.rule_id


@pytest.mark.parametrize(
    "driver, expected_rule",
    [
        ("contract_type", "CONTRACT_UPGRADE"),
        ("support_tickets", "SUPPORT_ESCALATION"),
        ("days_since_last_login", "RE_ENGAGEMENT"),
        ("monthly_usage_gb", "RE_ENGAGEMENT"),
        ("monthly_charges", "PRICE_REVIEW"),
        ("tech_support", "TECH_SUPPORT_TRIAL"),
        ("payment_method", "AUTOPAY_INCENTIVE"),
        ("tenure_months", "NEW_CUSTOMER_ONBOARDING"),
    ],
)
def test_strongest_risk_driver_selects_the_rule(driver, expected_rule):
    result = recommend("High", [factor(driver, 1.2), factor("internet_service", -0.3)])

    assert result.rule_id == expected_rule


def test_the_biggest_driver_wins_when_several_match():
    factors = [factor("support_tickets", 0.9), factor("contract_type", 0.5)]

    assert recommend("High", factors).rule_id == "SUPPORT_ESCALATION"


def test_factors_that_reduce_risk_are_not_treated_as_drivers():
    factors = [factor("contract_type", -0.9), factor("support_tickets", 0.4)]

    assert recommend("Medium", factors).rule_id == "SUPPORT_ESCALATION"


def test_fallback_when_no_rule_matches():
    result = recommend("Medium", [factor("tenure_months", -0.5)])

    assert result.rule_id == FALLBACK.rule_id
    assert "check-in" in result.action.lower()


@pytest.mark.parametrize("risk", ["Low", "Medium", "High"])
def test_every_suggestion_is_marked_for_human_review(risk):
    assert recommend(risk, [factor("contract_type", 0.7)]).requires_human_review is True


def test_rules_are_documented_and_unique():
    rule_ids = [rule.rule_id for rule in RULES]

    assert len(rule_ids) == len(set(rule_ids))
    assert all(rule.action and rule.description for rule in RULES)


def test_reason_mentions_the_driver():
    result = recommend("High", [factor("support_tickets", 1.0, value=9)])

    assert "support_tickets" in result.reason
    assert "9" in result.reason
