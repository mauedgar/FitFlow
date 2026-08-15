"""Unit tests for MembershipPlan to AllowedPlan access rules."""

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from app.core.enums import AllowedPlan, MembershipPlan
from app.services import errors as svc_errors
from app.services.class_schedule_service import validate_membership_access

if TYPE_CHECKING:
    from app.db.models.class_schedule import ClassSchedule
    from app.db.models.membership import Membership


def _membership(plan: MembershipPlan) -> "Membership":
    return cast("Membership", SimpleNamespace(plan=plan))


def _schedule(allowed_plan: AllowedPlan) -> "ClassSchedule":
    return cast("ClassSchedule", SimpleNamespace(allowed_plan=allowed_plan))


@pytest.mark.parametrize(
    ("membership_plan", "allowed_plan"),
    [
        (MembershipPlan.gym_only, AllowedPlan.gym_only),
        (MembershipPlan.classes, AllowedPlan.classes),
        (MembershipPlan.premium, AllowedPlan.gym_only),
        (MembershipPlan.premium, AllowedPlan.classes),
        (MembershipPlan.premium, AllowedPlan.premium),
        (MembershipPlan.personalized, AllowedPlan.gym_only),
        (MembershipPlan.personalized, AllowedPlan.classes),
        (MembershipPlan.personalized, AllowedPlan.premium),
        (MembershipPlan.personalized, AllowedPlan.personalized),
    ],
)
def test_membership_plan_can_access_its_allowed_schedule(
    membership_plan: MembershipPlan,
    allowed_plan: AllowedPlan,
) -> None:
    membership = _membership(membership_plan)
    schedule = _schedule(allowed_plan)

    validate_membership_access(membership, schedule)


def test_gym_only_membership_cannot_access_classes_schedule() -> None:
    membership = _membership(MembershipPlan.gym_only)
    schedule = _schedule(AllowedPlan.classes)

    with pytest.raises(svc_errors.BusinessValidationError):
        validate_membership_access(membership, schedule)
