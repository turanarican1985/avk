"""Read-oriented selectors for commercial access and scheduled charges."""

from __future__ import annotations

from django.db.models import QuerySet
from django.utils import timezone

from apps.access_billing.models import (
    AccessPlan,
    ChargeSchedule,
    ChargeScheduleStatus,
    Coupon,
    InstitutionAccessState,
)
from apps.institutions.models import Institution


def get_access_state_for_institution(
    *, institution: Institution
) -> InstitutionAccessState | None:
    """Return the commercial-access state for an institution, if any."""

    return (
        InstitutionAccessState.objects.select_related(
            "institution",
            "selected_plan",
            "active_payment_method",
        )
        .filter(institution=institution)
        .first()
    )


def get_current_charge_schedule_for_institution(
    *, institution: Institution
) -> ChargeSchedule | None:
    """Return the current relevant charge schedule for an institution."""

    return (
        ChargeSchedule.objects.select_related(
            "access_state",
            "plan",
            "coupon",
        )
        .filter(access_state__institution=institution)
        .exclude(status=ChargeScheduleStatus.CANCELLED)
        .order_by("-scheduled_for", "-created_at")
        .first()
    )


def list_due_charge_schedules(*, now=None) -> QuerySet[ChargeSchedule]:
    """Return charge schedules that are due for charging."""

    now = now or timezone.now()
    return ChargeSchedule.objects.select_related(
        "access_state", "plan", "coupon"
    ).filter(
        scheduled_for__lte=now,
        status__in=[ChargeScheduleStatus.PENDING, ChargeScheduleStatus.READY],
    )


def list_schedules_needing_seven_day_reminder(*, now=None) -> QuerySet[ChargeSchedule]:
    """Return charge schedules whose seven-day reminder boundary is due."""

    now = now or timezone.now()
    return ChargeSchedule.objects.select_related(
        "access_state", "plan", "coupon"
    ).filter(
        seven_day_reminder_due_at__lte=now,
        seven_day_reminder_marked_at__isnull=True,
        status__in=[ChargeScheduleStatus.PENDING, ChargeScheduleStatus.READY],
    )


def list_schedules_needing_three_day_reminder(*, now=None) -> QuerySet[ChargeSchedule]:
    """Return charge schedules whose three-day reminder boundary is due."""

    now = now or timezone.now()
    return ChargeSchedule.objects.select_related(
        "access_state", "plan", "coupon"
    ).filter(
        three_day_reminder_due_at__lte=now,
        three_day_reminder_marked_at__isnull=True,
        status__in=[ChargeScheduleStatus.PENDING, ChargeScheduleStatus.READY],
    )


def get_coupon_by_code(*, code: str) -> Coupon:
    """Return a coupon by case-insensitive code."""

    return Coupon.objects.get(code__iexact=code)


def list_active_plans() -> QuerySet[AccessPlan]:
    """Return active access plans."""

    return AccessPlan.objects.filter(is_active=True).order_by("duration_months")
