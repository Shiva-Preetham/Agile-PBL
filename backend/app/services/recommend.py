"""US08: transparent, rule-based retention actions.

How a suggestion is chosen:
1. Low-risk customers get LOW_RISK (no immediate action).
2. Otherwise, look at the risk drivers (factors that *increase* churn risk),
   strongest first, and use the rule for the first driver that has one.
3. If no driver has a rule, use the safe FALLBACK (a personal check-in call).

Every suggestion is marked `requires_human_review`: the system advises, and a
person decides.
"""
from dataclasses import dataclass

from app.services.explain import Factor


@dataclass(frozen=True)
class Rule:
    rule_id: str
    triggers: tuple[str, ...]  # customer fields that activate this rule
    action: str
    description: str


@dataclass(frozen=True)
class Recommendation:
    rule_id: str
    action: str
    reason: str
    requires_human_review: bool = True


RULES: tuple[Rule, ...] = (
    Rule("CONTRACT_UPGRADE", ("contract_type",),
         "Offer a discounted 12-month contract upgrade.",
         "Short contracts are the easiest to cancel; a longer contract with a discount builds commitment."),
    Rule("SUPPORT_ESCALATION", ("support_tickets",),
         "Escalate open issues to senior support and follow up within 48 hours.",
         "Many support tickets signal unresolved problems."),
    Rule("NEW_CUSTOMER_ONBOARDING", ("tenure_months",),
         "Assign an onboarding specialist and send a welcome-benefits pack.",
         "New customers have not yet seen the full value of the service."),
    Rule("RE_ENGAGEMENT", ("days_since_last_login", "monthly_usage_gb"),
         "Send a personalised re-engagement campaign highlighting unused features.",
         "Low activity usually comes before cancellation."),
    Rule("PRICE_REVIEW", ("monthly_charges", "total_charges"),
         "Review the plan and offer a loyalty discount or a better-fitting plan.",
         "High charges relative to value push customers to compare competitors."),
    Rule("TECH_SUPPORT_TRIAL", ("tech_support",),
         "Offer a free 3-month tech-support add-on.",
         "Customers without tech support struggle alone when problems occur."),
    Rule("AUTOPAY_INCENTIVE", ("payment_method",),
         "Encourage automatic payment (bank transfer / credit card) with a small incentive.",
         "Manual payment methods create a monthly decision point to leave."),
    Rule("SERVICE_QUALITY_CHECK", ("internet_service",),
         "Run a service-quality check on the customer's connection and follow up.",
         "Connection quality problems are a common reason to switch provider."),
)

LOW_RISK = Rule("LOW_RISK", (), "No immediate action. Continue regular engagement and monitor monthly.",
                "Customer is in the Low risk category.")
FALLBACK = Rule("FALLBACK", (), "Schedule a personal check-in call to understand the customer's concerns.",
                "Safe default when no specific rule matches.")

_RULE_FOR_FIELD = {field: rule for rule in RULES for field in rule.triggers}


def recommend(risk_category: str, factors: list[Factor]) -> Recommendation:
    if risk_category == "Low":
        return _build(LOW_RISK, LOW_RISK.description)

    drivers = sorted((f for f in factors if f.contribution > 0), key=lambda f: f.contribution, reverse=True)
    for driver in drivers:
        rule = _RULE_FOR_FIELD.get(driver.feature)
        if rule:
            return _build(rule, f"Top risk driver: {driver.label} = {driver.value}. {rule.description}")
    return _build(FALLBACK, FALLBACK.description)


def _build(rule: Rule, reason: str) -> Recommendation:
    return Recommendation(rule_id=rule.rule_id, action=rule.action, reason=reason)
