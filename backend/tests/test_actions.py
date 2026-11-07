"""US09: retention-action status rules.

Acceptance: Pending -> Contacted -> Completed transitions are allowed as
defined; invalid values are rejected.
"""
import pytest

from app.services.actions import (
    ACTION_STATUSES,
    InvalidStatusError,
    InvalidTransitionError,
    validate_transition,
)


def test_statuses_are_the_documented_ones():
    assert ACTION_STATUSES == ("Pending", "Contacted", "Completed")


@pytest.mark.parametrize("current, new", [("Pending", "Contacted"), ("Contacted", "Completed")])
def test_allowed_transitions(current, new):
    assert validate_transition(current, new) == new


@pytest.mark.parametrize("bad_status", ["Done", "", "pending ", "CLOSED"])
def test_unknown_status_is_rejected(bad_status):
    with pytest.raises(InvalidStatusError):
        validate_transition("Pending", bad_status)


@pytest.mark.parametrize(
    "current, new",
    [
        ("Pending", "Completed"),  # cannot skip contacting the customer
        ("Pending", "Pending"),
        ("Contacted", "Pending"),
        ("Completed", "Pending"),
        ("Completed", "Contacted"),
    ],
)
def test_disallowed_transitions_are_rejected(current, new):
    with pytest.raises(InvalidTransitionError):
        validate_transition(current, new)
