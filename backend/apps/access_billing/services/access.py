"""Write-oriented services for commercial access and scheduled charging."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

from apps.access_billing.models import (
    AccessPlan,
    ChargeAttempt,
    ChargeAttemptOutcome,
    ChargeSchedule,
    ChargeScheduleStatus,
    Coupon,
    InstitutionAccessState,
    InstitutionAccessStatus,
    PaymentMethodReference,
)
from apps.audit_core.services.recorder import AuditActor, AuditEvent, record_audit_event
from apps.institution_verification.selectors import institution_is_legally_approved
from apps.institutions.models import Institution

MONEY_QUANTIZE = Decimal("0.01")


class AccessBillingError(ValueError):
    """Base exception for commercial-access domain errors."""


class InvalidCouponApplication(AccessBillingError):
    """Raised when a coupon cannot be applied to a selected plan."""


class InvalidAccessStateTransition(AccessBillingError):
    """Raised when commercial-access lifecycle transitions are invalid."""


def quantize_money(amount: Decimal | str | float) -> Decimal:
    """Normalize currency values to a two-decimal representation."""

    return Decimal(str(amount)).quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP)


def create_access_plan(
    *,
    code: str,
    name: str,
    duration_months: int,
    base_price_amount: Decimal | str | float,
    currency: str = "TRY",
    is_active: bool = True,
) -> AccessPlan:
    """Create a selectable commercial access plan."""

    plan = AccessPlan(
        code=code,
        name=name,
        duration_months=duration_months,
        base_price_amount=quantize_money(base_price_amount),
        currency=currency,
        is_active=is_active,
    )
    plan.full_clean()
    plan.save()
    return plan


@transaction.atomic
def create_coupon(
    *,
    code: str,
    discount_percent: Decimal | str | float,
    applies_to_all_plans: bool = False,
    applicable_plans: list[AccessPlan] | None = None,
    valid_from=None,
    valid_until=None,
    usage_limit: int | None = None,
    is_active: bool = True,
) -> Coupon:
    """Create a percentage-based coupon with explicit applicability."""

    applicable_plans = applicable_plans or []
    if not applies_to_all_plans and not applicable_plans:
        raise InvalidCouponApplication(
            "Coupons must either apply to all plans or specify applicable plans."
        )

    coupon = Coupon(
        code=code.upper(),
        discount_percent=discount_percent,
        applies_to_all_plans=applies_to_all_plans,
        valid_from=valid_from,
        valid_until=valid_until,
        usage_limit=usage_limit,
        is_active=is_active,
    )
    coupon.full_clean()
    coupon.save()
    if applicable_plans:
        coupon.applicable_plans.set(applicable_plans)
    return coupon


def validate_coupon_for_plan(
    *,
    coupon: Coupon,
    plan: AccessPlan,
    at_time=None,
) -> Coupon:
    """Validate whether a coupon may apply to a selected plan."""

    at_time = at_time or timezone.now()
    if not coupon.is_active:
        raise InvalidCouponApplication("Coupon is not active.")
    if coupon.valid_from is not None and at_time < coupon.valid_from:
        raise InvalidCouponApplication("Coupon is not yet valid.")
    if coupon.valid_until is not None and at_time > coupon.valid_until:
        raise InvalidCouponApplication("Coupon has expired.")
    if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
        raise InvalidCouponApplication("Coupon usage limit has been reached.")
    if (
        not coupon.applies_to_all_plans
        and not coupon.applicable_plans.filter(id=plan.id).exists()
    ):
        raise InvalidCouponApplication("Coupon does not apply to the selected plan.")
    return coupon


def get_or_create_institution_access_state(
    *, institution: Institution
) -> InstitutionAccessState:
    """Return the institution's access state record, creating it if necessary."""

    access_state, _ = InstitutionAccessState.objects.get_or_create(
        institution=institution,
        defaults={"current_state": InstitutionAccessStatus.NOT_STARTED},
    )
    return access_state


@transaction.atomic
def mark_institution_eligible_for_access_start(
    *, institution: Institution
) -> InstitutionAccessState:
    """Mark an institution as eligible to start commercial access after approval."""

    if not institution_is_legally_approved(institution=institution):
        raise InvalidAccessStateTransition(
            "Commercial access can only become eligible after legal approval."
        )

    access_state = get_or_create_institution_access_state(institution=institution)
    if access_state.current_state == InstitutionAccessStatus.NOT_STARTED:
        access_state.current_state = InstitutionAccessStatus.ELIGIBLE_TO_START
        access_state.save(update_fields=["current_state", "updated_at"])
    return access_state


def capture_payment_method_reference(
    *,
    institution: Institution,
    provider_name: str,
    provider_customer_reference: str,
    provider_payment_method_reference: str,
    masked_display: str,
    card_brand: str = "",
    expiry_month: int | None = None,
    expiry_year: int | None = None,
) -> PaymentMethodReference:
    """Store safe payment-method metadata without raw card data."""

    return PaymentMethodReference.objects.create(
        institution=institution,
        provider_name=provider_name,
        provider_customer_reference=provider_customer_reference,
        provider_payment_method_reference=provider_payment_method_reference,
        masked_display=masked_display,
        card_brand=card_brand,
        expiry_month=expiry_month,
        expiry_year=expiry_year,
    )


def compute_discounted_amount(
    *, plan: AccessPlan, coupon: Coupon | None = None, at_time=None
) -> tuple[Decimal, Decimal]:
    """Compute the original and discounted amounts for a future charge."""

    original_amount = quantize_money(plan.base_price_amount)
    if coupon is None:
        return original_amount, original_amount

    validate_coupon_for_plan(coupon=coupon, plan=plan, at_time=at_time)
    discount_multiplier = (Decimal("100.00") - coupon.discount_percent) / Decimal(
        "100.00"
    )
    discounted_amount = quantize_money(original_amount * discount_multiplier)
    return original_amount, discounted_amount


def create_first_charge_schedule(
    *,
    access_state: InstitutionAccessState,
    plan: AccessPlan,
    coupon: Coupon | None,
    original_amount: Decimal,
    discounted_amount: Decimal,
    scheduled_for,
) -> ChargeSchedule:
    """Create the first scheduled charge at the end of the access period."""

    return ChargeSchedule.objects.create(
        access_state=access_state,
        plan=plan,
        coupon=coupon,
        original_amount=original_amount,
        discounted_amount=discounted_amount,
        currency=plan.currency,
        scheduled_for=scheduled_for,
        status=ChargeScheduleStatus.PENDING,
        seven_day_reminder_due_at=scheduled_for - relativedelta(days=7),
        three_day_reminder_due_at=scheduled_for - relativedelta(days=3),
    )


@transaction.atomic
def start_full_feature_access_period(
    *,
    institution: Institution,
    plan: AccessPlan,
    payment_method_payload: dict,
    coupon: Coupon | None = None,
    actor_id: str | None = None,
) -> InstitutionAccessState:
    """Start the one-month full-feature access period for an approved institution."""

    access_state = mark_institution_eligible_for_access_start(institution=institution)
    if access_state.current_state != InstitutionAccessStatus.ELIGIBLE_TO_START:
        raise InvalidAccessStateTransition(
            "Commercial access can only start from the eligible-to-start state."
        )
    if not plan.is_active:
        raise InvalidAccessStateTransition("Inactive plans cannot be selected.")

    payment_method = capture_payment_method_reference(
        institution=institution,
        **payment_method_payload,
    )
    coupon_to_apply = None
    if coupon is not None:
        coupon_to_apply = validate_coupon_for_plan(coupon=coupon, plan=plan)

    original_amount, discounted_amount = compute_discounted_amount(
        plan=plan,
        coupon=coupon_to_apply,
        at_time=timezone.now(),
    )
    access_period_started_at = timezone.now()
    access_period_ends_at = access_period_started_at + relativedelta(months=1)
    charge_schedule = create_first_charge_schedule(
        access_state=access_state,
        plan=plan,
        coupon=coupon_to_apply,
        original_amount=original_amount,
        discounted_amount=discounted_amount,
        scheduled_for=access_period_ends_at,
    )

    access_state.current_state = InstitutionAccessStatus.ACCESS_ACTIVE
    access_state.access_period_started_at = access_period_started_at
    access_state.access_period_ends_at = access_period_ends_at
    access_state.selected_plan = plan
    access_state.active_payment_method = payment_method
    access_state.scheduled_first_charge_at = charge_schedule.scheduled_for
    access_state.recovery_started_at = None
    access_state.save(
        update_fields=[
            "current_state",
            "access_period_started_at",
            "access_period_ends_at",
            "selected_plan",
            "active_payment_method",
            "scheduled_first_charge_at",
            "recovery_started_at",
            "updated_at",
        ]
    )

    if coupon_to_apply is not None:
        coupon_to_apply.usage_count += 1
        coupon_to_apply.save(update_fields=["usage_count", "updated_at"])

    record_audit_event(
        AuditEvent(
            event_name="access_billing.access_started",
            actor=(
                AuditActor(actor_id=actor_id, actor_type="user")
                if actor_id is not None
                else None
            ),
            target_type="institution_access_state",
            target_id=str(access_state.id),
            metadata={
                "institution_id": str(institution.id),
                "plan_id": str(plan.id),
                "charge_schedule_id": str(charge_schedule.id),
                "coupon_code": coupon_to_apply.code if coupon_to_apply else None,
            },
        )
    )
    return access_state


def _ensure_reminder_can_be_marked(
    *, charge_schedule: ChargeSchedule, due_at, already_marked_at
) -> None:
    """Validate reminder marking against the configured due boundaries."""

    if charge_schedule.status in {
        ChargeScheduleStatus.CHARGE_SUCCEEDED,
        ChargeScheduleStatus.CANCELLED,
    }:
        raise InvalidAccessStateTransition(
            "Reminders cannot be marked for completed or cancelled schedules."
        )
    if due_at is None or timezone.now() < due_at:
        raise InvalidAccessStateTransition("This reminder is not due yet.")
    if already_marked_at is not None:
        raise InvalidAccessStateTransition("This reminder was already marked.")


@transaction.atomic
def mark_seven_day_reminder_due(*, charge_schedule: ChargeSchedule) -> ChargeSchedule:
    """Mark the seven-day reminder boundary as due."""

    _ensure_reminder_can_be_marked(
        charge_schedule=charge_schedule,
        due_at=charge_schedule.seven_day_reminder_due_at,
        already_marked_at=charge_schedule.seven_day_reminder_marked_at,
    )
    charge_schedule.seven_day_reminder_marked_at = timezone.now()
    charge_schedule.save(update_fields=["seven_day_reminder_marked_at", "updated_at"])

    access_state = charge_schedule.access_state
    if access_state.current_state == InstitutionAccessStatus.ACCESS_ACTIVE:
        access_state.current_state = InstitutionAccessStatus.ACCESS_EXPIRING_SOON
        access_state.save(update_fields=["current_state", "updated_at"])
    return charge_schedule


@transaction.atomic
def mark_three_day_reminder_due(*, charge_schedule: ChargeSchedule) -> ChargeSchedule:
    """Mark the three-day reminder boundary as due."""

    _ensure_reminder_can_be_marked(
        charge_schedule=charge_schedule,
        due_at=charge_schedule.three_day_reminder_due_at,
        already_marked_at=charge_schedule.three_day_reminder_marked_at,
    )
    charge_schedule.three_day_reminder_marked_at = timezone.now()
    charge_schedule.save(update_fields=["three_day_reminder_marked_at", "updated_at"])

    access_state = charge_schedule.access_state
    if access_state.current_state in {
        InstitutionAccessStatus.ACCESS_ACTIVE,
        InstitutionAccessStatus.ACCESS_EXPIRING_SOON,
    }:
        access_state.current_state = InstitutionAccessStatus.AWAITING_FIRST_CHARGE
        access_state.save(update_fields=["current_state", "updated_at"])
    return charge_schedule


def _create_charge_attempt(
    *,
    charge_schedule: ChargeSchedule,
    outcome: ChargeAttemptOutcome | str,
    captured_amount: Decimal | str | float | None = None,
    provider_name: str = "",
    provider_attempt_reference: str = "",
    failure_code: str = "",
    failure_reason: str = "",
) -> ChargeAttempt:
    """Persist a charge attempt record."""

    return ChargeAttempt.objects.create(
        charge_schedule=charge_schedule,
        provider_name=provider_name,
        provider_attempt_reference=provider_attempt_reference,
        attempted_at=timezone.now(),
        outcome=outcome,
        failure_code=failure_code,
        failure_reason=failure_reason,
        captured_amount=(
            quantize_money(captured_amount) if captured_amount is not None else None
        ),
    )


@transaction.atomic
def record_successful_charge_attempt(
    *,
    charge_schedule: ChargeSchedule,
    captured_amount: Decimal | str | float,
    provider_name: str = "",
    provider_attempt_reference: str = "",
) -> ChargeAttempt:
    """Record a successful charge attempt and move access into a paid-active state."""

    attempt = _create_charge_attempt(
        charge_schedule=charge_schedule,
        outcome=ChargeAttemptOutcome.SUCCEEDED,
        captured_amount=captured_amount,
        provider_name=provider_name,
        provider_attempt_reference=provider_attempt_reference,
    )
    charge_schedule.status = ChargeScheduleStatus.CHARGE_SUCCEEDED
    charge_schedule.save(update_fields=["status", "updated_at"])

    access_state = charge_schedule.access_state
    access_state.current_state = InstitutionAccessStatus.PAID_ACTIVE
    access_state.last_charge_success_at = attempt.attempted_at
    access_state.recovery_started_at = None
    access_state.save(
        update_fields=[
            "current_state",
            "last_charge_success_at",
            "recovery_started_at",
            "updated_at",
        ]
    )
    return attempt


@transaction.atomic
def record_failed_charge_attempt(
    *,
    charge_schedule: ChargeSchedule,
    provider_name: str = "",
    provider_attempt_reference: str = "",
    failure_code: str = "",
    failure_reason: str = "",
) -> ChargeAttempt:
    """Record a failed charge attempt and move access into recovery-oriented state."""

    attempt = _create_charge_attempt(
        charge_schedule=charge_schedule,
        outcome=ChargeAttemptOutcome.FAILED,
        provider_name=provider_name,
        provider_attempt_reference=provider_attempt_reference,
        failure_code=failure_code,
        failure_reason=failure_reason,
    )
    charge_schedule.status = ChargeScheduleStatus.CHARGE_FAILED
    charge_schedule.save(update_fields=["status", "updated_at"])

    access_state = charge_schedule.access_state
    access_state.current_state = InstitutionAccessStatus.PAYMENT_FAILED
    access_state.last_charge_failure_at = attempt.attempted_at
    access_state.recovery_started_at = attempt.attempted_at
    access_state.save(
        update_fields=[
            "current_state",
            "last_charge_failure_at",
            "recovery_started_at",
            "updated_at",
        ]
    )
    return attempt
