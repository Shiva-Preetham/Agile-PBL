"""US14: Next Best Action and a step-by-step retention plan.

How it works, in plain words:

1. Take a copy of the customer and pretend we did one retention action
   (e.g. "offer a 12-month contract" means contract_type becomes "One year").
2. Ask the churn model again. The drop in its score is the estimated benefit.
3. Do this for every action that applies to the customer and rank them.
   The top one is the **Next Best Action**.
4. Retention plan: apply the best action, then look for the next best on
   top of it, and repeat until the customer is Low risk or nothing helps.

The score drop is measured in log-odds (the same unit as SHAP), because
probabilities flatten out near 100%, where every action would look tiny.
These are model "what-if" estimates, not guarantees, so a person decides.
"""
import math
from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from app.services.explain import Explanation
from app.services.fields import FIELD_LABELS, ID_COLUMN
from app.services.prediction import get_predictor
from app.services.recommend import RULES, Recommendation, recommend
from app.services.risk import classify_risk

MIN_SCORE_DROP = 0.10  # smallest log-odds drop that counts as "this helps"

# Documented assumptions about what each action changes.
RESOLVED_TICKETS = 1  # escalation resolves open issues down to one ticket
SUPPORT_TICKETS_TRIGGER = 2
INACTIVE_DAYS_TRIGGER = 7
DAYS_SINCE_LOGIN_AFTER_CAMPAIGN = 3
HIGH_CHARGES_TRIGGER = 70.0
LOYALTY_DISCOUNT = 0.15
COST_RANK = {"Low": 0, "Medium": 1, "High": 2}


@dataclass(frozen=True)
class Effect:
    cost: str
    simulate: Callable[[dict], dict | None]  # changed fields, or None if the action does not apply


def _contract_upgrade(c):
    return {"contract_type": "One year"} if c["contract_type"] == "Month-to-month" else None


def _support_escalation(c):
    return {"support_tickets": RESOLVED_TICKETS} if c["support_tickets"] >= SUPPORT_TICKETS_TRIGGER else None


def _re_engagement(c):
    if c["days_since_last_login"] > INACTIVE_DAYS_TRIGGER:
        return {"days_since_last_login": DAYS_SINCE_LOGIN_AFTER_CAMPAIGN}
    return None


def _price_review(c):
    if c["monthly_charges"] >= HIGH_CHARGES_TRIGGER:
        return {"monthly_charges": round(c["monthly_charges"] * (1 - LOYALTY_DISCOUNT), 2)}
    return None


def _tech_support_trial(c):
    return {"tech_support": "Yes"} if c["tech_support"] == "No" and c["internet_service"] != "No" else None


def _autopay_incentive(c):
    return {"payment_method": "Bank transfer"} if c["payment_method"] in ("Electronic check", "Mailed check") else None


EFFECTS: dict[str, Effect] = {
    "CONTRACT_UPGRADE": Effect("Medium", _contract_upgrade),
    "SUPPORT_ESCALATION": Effect("Low", _support_escalation),
    "RE_ENGAGEMENT": Effect("Low", _re_engagement),
    "PRICE_REVIEW": Effect("High", _price_review),
    "TECH_SUPPORT_TRIAL": Effect("Medium", _tech_support_trial),
    "AUTOPAY_INCENTIVE": Effect("Low", _autopay_incentive),
}
_RULES = {rule.rule_id: rule for rule in RULES}
_SIMULATED_FIELDS = {field for rule in RULES if rule.rule_id in EFFECTS for field in rule.triggers}


@dataclass(frozen=True)
class ActionOption:
    rule_id: str
    action: str
    cost: str
    changes: dict
    change_text: list[str]
    current_probability: float
    new_probability: float
    score_drop: float

    @property
    def reduction(self) -> float:
        return self.current_probability - self.new_probability

    @property
    def new_risk(self) -> str:
        return classify_risk(self.new_probability)


@dataclass(frozen=True)
class PlanStep:
    rule_id: str
    action: str
    changes: dict
    probability: float  # estimated churn after this step (and all before it)

    @property
    def risk(self) -> str:
        return classify_risk(self.probability)


@dataclass(frozen=True)
class NextBestAction:
    customer_id: str
    current_probability: float
    current_risk: str
    best: Recommendation
    options: list[ActionOption]
    plan: list[PlanStep]


def candidate_changes(customer: dict) -> dict[str, dict]:
    """The actions that apply to this customer, with the fields each would change."""
    candidates = {}
    for rule_id, effect in EFFECTS.items():
        changes = effect.simulate(customer)
        if changes:
            candidates[rule_id] = changes
    return candidates


def next_best_actions(data: pd.DataFrame, explanations: list[Explanation]) -> list[NextBestAction]:
    """One Next Best Action (+ options and plan) per row of validated customer data."""
    records = data.to_dict(orient="records")
    current = [float(p) for p in get_predictor().predict_proba(data)]
    eligible = [candidate_changes(r) if classify_risk(p) != "Low" else {} for r, p in zip(records, current)]

    options = _rank_single_actions(records, current, eligible, list(data.columns))
    plans = _build_plans(records, current, eligible, list(data.columns))

    results = []
    for i, record in enumerate(records):
        risk = classify_risk(current[i])
        results.append(NextBestAction(
            customer_id=record[ID_COLUMN],
            current_probability=current[i],
            current_risk=risk,
            best=_best_recommendation(risk, options[i], explanations[i]),
            options=options[i],
            plan=plans[i],
        ))
    return results


def _rank_single_actions(records, current, eligible, columns) -> list[list[ActionOption]]:
    trials = [(i, rule_id, {**records[i], **changes}) for i in range(len(records))
              for rule_id, changes in eligible[i].items()]
    ranked: list[list[ActionOption]] = [[] for _ in records]
    for (i, rule_id, _), probability in zip(trials, _predict(trials, columns)):
        drop = _log_odds(current[i]) - _log_odds(probability)
        if drop >= MIN_SCORE_DROP:
            changes = eligible[i][rule_id]
            ranked[i].append(ActionOption(
                rule_id=rule_id,
                action=_RULES[rule_id].action,
                cost=EFFECTS[rule_id].cost,
                changes=changes,
                change_text=[f"{FIELD_LABELS[f]}: {records[i][f]} → {v}" for f, v in changes.items()],
                current_probability=current[i],
                new_probability=probability,
                score_drop=drop,
            ))
    for customer_options in ranked:
        customer_options.sort(key=lambda o: (-o.score_drop, COST_RANK[o.cost]))
    return ranked


def _build_plans(records, current, eligible, columns) -> list[list[PlanStep]]:
    """Greedy plan: keep adding the action that helps most on top of the previous ones."""
    plans: list[list[PlanStep]] = [[] for _ in records]
    applied: list[dict] = [{} for _ in records]  # fields changed so far by each customer's plan
    probability = list(current)
    active = [i for i in range(len(records)) if eligible[i]]

    while active:
        trials = [
            (i, rule_id, {**records[i], **applied[i], **changes})
            for i in active
            for rule_id, changes in eligible[i].items()
            if rule_id not in {step.rule_id for step in plans[i]}
        ]
        best: dict[int, tuple[float, int, str, float]] = {}
        for (i, rule_id, _), new_probability in zip(trials, _predict(trials, columns)):
            drop = _log_odds(probability[i]) - _log_odds(new_probability)
            key = (drop, -COST_RANK[EFFECTS[rule_id].cost])
            if i not in best or key > best[i][:2]:
                best[i] = (*key, rule_id, new_probability)

        still_active = []
        for i in active:
            if i not in best or best[i][0] < MIN_SCORE_DROP:
                continue  # nothing left that helps enough
            _, _, rule_id, new_probability = best[i]
            applied[i].update(eligible[i][rule_id])
            probability[i] = new_probability
            plans[i].append(PlanStep(rule_id, _RULES[rule_id].action, eligible[i][rule_id], new_probability))
            if classify_risk(new_probability) != "Low" and len(plans[i]) < len(eligible[i]):
                still_active.append(i)
        active = still_active
    return plans


def _best_recommendation(risk: str, options: list[ActionOption], explanation: Explanation) -> Recommendation:
    if risk != "Low" and options:
        top = options[0]
        reason = (
            f"Estimated churn {top.current_probability:.0%} → {top.new_probability:.0%} "
            f"if: {'; '.join(top.change_text)}. {_RULES[top.rule_id].description}"
        )
        return Recommendation(rule_id=top.rule_id, action=top.action, reason=reason)
    # No simulated action helps enough: use the rule for the strongest driver we cannot simulate
    # (e.g. onboarding for new customers), or the safe check-in-call fallback.
    other_drivers = [f for f in explanation.factors if f.feature not in _SIMULATED_FIELDS]
    return recommend(risk, other_drivers)


def _predict(trials, columns) -> list[float]:
    if not trials:
        return []
    frame = pd.DataFrame([row for _, _, row in trials])[columns]
    return [float(p) for p in get_predictor().predict_proba(frame)]


def _log_odds(probability: float) -> float:
    p = min(max(probability, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))
