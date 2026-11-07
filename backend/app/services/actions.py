"""US09: retention-action tracking.

Workflow (one direction only, so the history stays meaningful):

    Pending  ->  Contacted  ->  Completed
"""
from sqlalchemy.orm import Session

from app.models import Customer, RetentionAction
from app.services.recommend import Recommendation

ACTION_STATUSES = ("Pending", "Contacted", "Completed")
ALLOWED_TRANSITIONS = {
    "Pending": ("Contacted",),
    "Contacted": ("Completed",),
    "Completed": (),
}
AT_RISK_CATEGORIES = ("Medium", "High")


class InvalidStatusError(ValueError):
    pass


class InvalidTransitionError(ValueError):
    pass


def validate_transition(current: str, new: str) -> str:
    if new not in ACTION_STATUSES:
        raise InvalidStatusError(f"'{new}' is not a valid status. Use one of: {', '.join(ACTION_STATUSES)}.")
    allowed = ALLOWED_TRANSITIONS[current]
    if new not in allowed:
        next_step = ", ".join(allowed) or "none (the action is already completed)"
        raise InvalidTransitionError(f"Cannot move from {current} to {new}. Allowed next status: {next_step}.")
    return new


def sync_actions(db: Session, customers: list[Customer], recommendations: list[Recommendation]) -> None:
    """Create a Pending action for every at-risk customer; refresh the suggestion
    text for existing actions without touching their status."""
    for customer, recommendation in zip(customers, recommendations):
        if customer.action is not None:
            customer.action.rule_id = recommendation.rule_id
            customer.action.action = recommendation.action
        elif customer.risk_category in AT_RISK_CATEGORIES:
            customer.action = RetentionAction(
                rule_id=recommendation.rule_id, action=recommendation.action, status="Pending"
            )
    db.commit()


def update_status(db: Session, action: RetentionAction, new_status: str) -> RetentionAction:
    action.status = validate_transition(action.status, new_status)
    db.commit()
    return action
