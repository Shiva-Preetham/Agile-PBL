"""US14: Next Best Action for a specific customer.

Acceptance: only actions that apply to the customer are simulated; each
option shows the estimated churn after the action; options are ranked and
the top one is the Next Best Action; a step-by-step plan adds actions until
the customer is Low risk or nothing more helps; suggestions need human
review; Low-risk customers get no action.
"""
import math

import pandas as pd
import pytest

from app.services import next_best_action as nba
from app.services.explain import explain
from app.services.next_best_action import EFFECTS, candidate_changes, next_best_actions
from app.services.prediction import get_predictor
from app.services.validation import validate_dataframe
from tests.conftest import at_risk_row, loyal_row, make_row, risky_row


def clean(*rows):
    return validate_dataframe(pd.DataFrame(list(rows))).data


def record(row):
    return clean(row).to_dict(orient="records")[0]


def plan_for(row):
    data = clean(row)
    return next_best_actions(data, explain(data))[0]


def rescore(row, changes):
    features = {k: v for k, v in record(row).items() if k != "customer_id"}
    features.update(changes)
    return get_predictor().predict_one(features)


def log_odds(p):
    return math.log(p / (1 - p))


# ---------- which actions apply to this customer ----------

def test_customer_with_every_problem_is_eligible_for_every_simulated_action():
    assert set(candidate_changes(record(risky_row()))) == set(EFFECTS)


def test_loyal_customer_is_eligible_for_no_action():
    assert candidate_changes(record(loyal_row())) == {}


def test_contract_upgrade_only_changes_the_contract():
    assert candidate_changes(record(at_risk_row()))["CONTRACT_UPGRADE"] == {"contract_type": "One year"}


def test_loyalty_discount_lowers_monthly_charges_by_15_percent():
    assert candidate_changes(record(at_risk_row()))["PRICE_REVIEW"] == {"monthly_charges": 72.25}


# ---------- ranking single actions ----------

def test_options_are_ranked_by_how_much_they_lower_the_score():
    drops = [o.score_drop for o in plan_for(at_risk_row()).options]

    assert len(drops) >= 2
    assert drops == sorted(drops, reverse=True)


def test_every_option_lowers_churn_by_a_meaningful_amount():
    plan = plan_for(at_risk_row())

    for option in plan.options:
        assert option.new_probability < plan.current_probability
        assert option.score_drop >= nba.MIN_SCORE_DROP


def test_estimate_equals_rescoring_the_changed_customer():
    option = plan_for(at_risk_row()).options[0]

    assert option.new_probability == pytest.approx(rescore(at_risk_row(), option.changes))


def test_score_drop_is_measured_in_log_odds_like_shap():
    plan = plan_for(at_risk_row())
    option = plan.options[0]

    assert option.score_drop == pytest.approx(log_odds(plan.current_probability) - log_odds(option.new_probability))


def test_change_is_described_in_plain_words():
    option = next(o for o in plan_for(at_risk_row()).options if o.rule_id == "CONTRACT_UPGRADE")

    assert option.change_text == ["Contract type: Month-to-month → One year"]


# ---------- the Next Best Action ----------

def test_next_best_action_is_the_top_option_and_needs_human_review():
    plan = plan_for(at_risk_row())

    assert plan.best.rule_id == plan.options[0].rule_id
    assert plan.best.requires_human_review is True
    assert "→" in plan.best.reason


def test_low_risk_customer_gets_no_immediate_action():
    plan = plan_for(loyal_row())

    assert plan.best.rule_id == "LOW_RISK"
    assert plan.options == []
    assert plan.plan == []


def test_falls_back_to_a_non_simulated_rule_when_nothing_helps_enough(monkeypatch):
    monkeypatch.setattr(nba, "MIN_SCORE_DROP", 99.0)

    plan = plan_for(risky_row())

    assert plan.options == []
    assert plan.best.rule_id not in EFFECTS
    assert plan.best.requires_human_review is True


# ---------- the step-by-step retention plan ----------

def test_plan_starts_with_the_next_best_action():
    plan = plan_for(at_risk_row())

    assert plan.plan[0].rule_id == plan.best.rule_id


def test_each_plan_step_lowers_churn_further():
    plan = plan_for(at_risk_row())
    probabilities = [plan.current_probability] + [step.probability for step in plan.plan]

    assert all(later < earlier for earlier, later in zip(probabilities, probabilities[1:]))
    assert len({step.rule_id for step in plan.plan}) == len(plan.plan)


def test_plan_stops_as_soon_as_the_customer_is_low_risk():
    for row in (at_risk_row(), risky_row()):
        steps = plan_for(row).plan
        assert all(step.risk != "Low" for step in steps[:-1])


def test_final_plan_estimate_equals_rescoring_with_all_changes():
    plan = plan_for(risky_row())
    all_changes = {}
    for step in plan.plan:
        all_changes.update(step.changes)

    assert plan.plan[-1].probability == pytest.approx(rescore(risky_row(), all_changes))


def test_plan_ends_at_low_risk_or_when_nothing_else_helps():
    row = risky_row()
    plan = plan_for(row)
    if plan.plan[-1].risk == "Low":
        return
    applied = {}
    for step in plan.plan:
        applied.update(step.changes)
    after_plan = rescore(row, applied)
    used = {step.rule_id for step in plan.plan}
    for rule_id, changes in candidate_changes(record(row)).items():
        if rule_id not in used:
            assert log_odds(after_plan) - log_odds(rescore(row, {**applied, **changes})) < nba.MIN_SCORE_DROP


def test_one_result_per_customer_in_input_order():
    data = clean(at_risk_row("A"), loyal_row("B"), make_row("C"))

    results = next_best_actions(data, explain(data))

    assert [r.customer_id for r in results] == ["A", "B", "C"]
