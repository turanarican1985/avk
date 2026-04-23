"""Behavior tests for the commercial-access foundation."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.access_billing.models import (
    ChargeScheduleStatus,
    InstitutionAccessState,
    InstitutionAccessStatus,
    PaymentMethodReference,
)
from apps.access_billing.selectors import (
    get_current_charge_schedule_for_institution,
    list_schedules_needing_seven_day_reminder,
    list_schedules_needing_three_day_reminder,
)
from apps.access_billing.services import (
    InvalidAccessStateTransition,
    InvalidCouponApplication,
    create_access_plan,
    create_coupon,
    mark_seven_day_reminder_due,
    mark_three_day_reminder_due,
    record_failed_charge_attempt,
    record_successful_charge_attempt,
    start_full_feature_access_period,
    validate_coupon_for_plan,
)
from apps.institution_verification.models import (
    InstitutionVerificationCase,
    VerificationCaseStatus,
)
from apps.institutions.models import InstitutionType
from apps.institutions.services import attach_owner_membership, create_institution


@pytest.fixture
def institution_user():
    return get_user_model().objects.create_user(
        email="billing-owner@example.com",
        password="testpass123",
    )


@pytest.fixture
def institution(institution_user):
    institution = create_institution(
        legal_name="Arslan Hukuk",
        display_name="Arslan Hukuk",
        slug="arslan-hukuk",
        institution_type=InstitutionType.TEAM_BASED,
    )
    attach_owner_membership(institution=institution, user=institution_user)
    return institution


@pytest.fixture
def approved_institution(institution):
    InstitutionVerificationCase.objects.create(
        institution=institution,
        status=VerificationCaseStatus.APPROVED,
    )
    return institution


@pytest.fixture
def one_month_plan():
    return create_access_plan(
        code="basic-1m",
        name="Basic 1 Month",
        duration_months=1,
        base_price_amount=Decimal("1000.00"),
        currency="TRY",
    )


@pytest.fixture
def three_month_plan():
    return create_access_plan(
        code="basic-3m",
        name="Basic 3 Months",
        duration_months=3,
        base_price_amount=Decimal("2500.00"),
        currency="TRY",
    )


@pytest.fixture
def payment_method_payload():
    return {
        "provider_name": "mockpay",
        "provider_customer_reference": "cust-123",
        "provider_payment_method_reference": "pm-123",
        "masked_display": "**** **** **** 4242",
        "card_brand": "Visa",
        "expiry_month": 12,
        "expiry_year": 2030,
    }


@pytest.mark.django_db
def test_create_valid_plan():
    plan = create_access_plan(
        code="pro-6m",
        name="Pro 6 Months",
        duration_months=6,
        base_price_amount=Decimal("6000.00"),
        currency="TRY",
    )

    assert plan.duration_months == 6
    assert plan.base_price_amount == Decimal("6000.00")


@pytest.mark.django_db
def test_create_valid_coupon(one_month_plan, three_month_plan):
    coupon = create_coupon(
        code="SUMMER20",
        discount_percent=Decimal("20.00"),
        applicable_plans=[one_month_plan, three_month_plan],
    )

    assert coupon.code == "SUMMER20"
    assert coupon.discount_percent == Decimal("20.00")
    assert coupon.applicable_plans.count() == 2


@pytest.mark.django_db
def test_invalid_coupon_percent_rejected(one_month_plan):
    with pytest.raises(ValidationError):
        create_coupon(
            code="FREE100",
            discount_percent=Decimal("100.00"),
            applicable_plans=[one_month_plan],
        )


@pytest.mark.django_db
def test_coupon_applicability_to_allowed_plan_period_works(
    one_month_plan, three_month_plan
):
    coupon = create_coupon(
        code="ONEONLY",
        discount_percent=Decimal("15.00"),
        applicable_plans=[one_month_plan],
    )

    validated_coupon = validate_coupon_for_plan(coupon=coupon, plan=one_month_plan)

    assert validated_coupon.id == coupon.id
    with pytest.raises(InvalidCouponApplication):
        validate_coupon_for_plan(coupon=coupon, plan=three_month_plan)


@pytest.mark.django_db
def test_coupon_cannot_apply_to_disallowed_plan_period(
    one_month_plan, three_month_plan
):
    coupon = create_coupon(
        code="THREEONLY",
        discount_percent=Decimal("25.00"),
        applicable_plans=[three_month_plan],
    )

    with pytest.raises(InvalidCouponApplication):
        validate_coupon_for_plan(coupon=coupon, plan=one_month_plan)


@pytest.mark.django_db
def test_institution_cannot_start_commercial_access_if_not_legally_approved(
    institution,
    one_month_plan,
    payment_method_payload,
):
    with pytest.raises(InvalidAccessStateTransition):
        start_full_feature_access_period(
            institution=institution,
            plan=one_month_plan,
            payment_method_payload=payment_method_payload,
        )


@pytest.mark.django_db
def test_legally_approved_institution_can_start_access(
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    access_state = start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    assert access_state.current_state == InstitutionAccessStatus.ACCESS_ACTIVE
    assert access_state.access_period_started_at is not None
    assert access_state.access_period_ends_at is not None


@pytest.mark.django_db
def test_starting_access_captures_payment_method_reference_boundary(
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    access_state = start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    assert access_state.active_payment_method is not None
    assert access_state.active_payment_method.masked_display == "**** **** **** 4242"


@pytest.mark.django_db
def test_starting_access_with_selected_plan_creates_charge_schedule(
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    charge_schedule = get_current_charge_schedule_for_institution(
        institution=approved_institution
    )
    assert charge_schedule is not None
    assert charge_schedule.plan == one_month_plan
    assert charge_schedule.status == ChargeScheduleStatus.PENDING


@pytest.mark.django_db
def test_scheduled_charge_is_set_to_access_period_end(
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    access_state = start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    charge_schedule = get_current_charge_schedule_for_institution(
        institution=approved_institution
    )
    assert charge_schedule.scheduled_for == access_state.access_period_ends_at
    assert access_state.scheduled_first_charge_at == access_state.access_period_ends_at


@pytest.mark.django_db
def test_valid_coupon_reduces_scheduled_amount(
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    coupon = create_coupon(
        code="SAVE25",
        discount_percent=Decimal("25.00"),
        applicable_plans=[one_month_plan],
    )

    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
        coupon=coupon,
    )

    charge_schedule = get_current_charge_schedule_for_institution(
        institution=approved_institution
    )
    assert charge_schedule.original_amount == Decimal("1000.00")
    assert charge_schedule.discounted_amount == Decimal("750.00")


@pytest.mark.django_db
def test_invalid_coupon_is_rejected(
    approved_institution,
    one_month_plan,
    three_month_plan,
    payment_method_payload,
):
    coupon = create_coupon(
        code="THREEMONTH",
        discount_percent=Decimal("10.00"),
        applicable_plans=[three_month_plan],
    )

    with pytest.raises(InvalidCouponApplication):
        start_full_feature_access_period(
            institution=approved_institution,
            plan=one_month_plan,
            payment_method_payload=payment_method_payload,
            coupon=coupon,
        )


@pytest.mark.django_db
def test_seven_day_reminder_selection_works(
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )
    charge_schedule = get_current_charge_schedule_for_institution(
        institution=approved_institution
    )
    charge_schedule.seven_day_reminder_due_at = timezone.now() - timedelta(minutes=1)
    charge_schedule.save(update_fields=["seven_day_reminder_due_at", "updated_at"])

    due_schedules = list(list_schedules_needing_seven_day_reminder())

    assert charge_schedule in due_schedules
    mark_seven_day_reminder_due(charge_schedule=charge_schedule)
    charge_schedule.refresh_from_db()
    access_state = InstitutionAccessState.objects.get(institution=approved_institution)
    assert charge_schedule.seven_day_reminder_marked_at is not None
    assert access_state.current_state == InstitutionAccessStatus.ACCESS_EXPIRING_SOON


@pytest.mark.django_db
def test_three_day_reminder_selection_works(
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )
    charge_schedule = get_current_charge_schedule_for_institution(
        institution=approved_institution
    )
    charge_schedule.three_day_reminder_due_at = timezone.now() - timedelta(minutes=1)
    charge_schedule.save(update_fields=["three_day_reminder_due_at", "updated_at"])

    due_schedules = list(list_schedules_needing_three_day_reminder())

    assert charge_schedule in due_schedules
    mark_three_day_reminder_due(charge_schedule=charge_schedule)
    charge_schedule.refresh_from_db()
    access_state = InstitutionAccessState.objects.get(institution=approved_institution)
    assert charge_schedule.three_day_reminder_marked_at is not None
    assert access_state.current_state == InstitutionAccessStatus.AWAITING_FIRST_CHARGE


@pytest.mark.django_db
def test_successful_charge_attempt_moves_state_into_paid_active_direction(
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )
    charge_schedule = get_current_charge_schedule_for_institution(
        institution=approved_institution
    )

    attempt = record_successful_charge_attempt(
        charge_schedule=charge_schedule,
        captured_amount=Decimal("1000.00"),
        provider_name="mockpay",
        provider_attempt_reference="attempt-1",
    )

    charge_schedule.refresh_from_db()
    access_state = InstitutionAccessState.objects.get(institution=approved_institution)
    assert attempt.outcome == "succeeded"
    assert charge_schedule.status == ChargeScheduleStatus.CHARGE_SUCCEEDED
    assert access_state.current_state == InstitutionAccessStatus.PAID_ACTIVE


@pytest.mark.django_db
def test_failed_charge_attempt_moves_state_into_failure_recovery_direction(
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )
    charge_schedule = get_current_charge_schedule_for_institution(
        institution=approved_institution
    )

    attempt = record_failed_charge_attempt(
        charge_schedule=charge_schedule,
        provider_name="mockpay",
        provider_attempt_reference="attempt-2",
        failure_code="declined",
        failure_reason="Issuer declined the charge.",
    )

    charge_schedule.refresh_from_db()
    access_state = InstitutionAccessState.objects.get(institution=approved_institution)
    assert attempt.outcome == "failed"
    assert charge_schedule.status == ChargeScheduleStatus.CHARGE_FAILED
    assert access_state.current_state == InstitutionAccessStatus.PAYMENT_FAILED
    assert access_state.recovery_started_at is not None


@pytest.mark.django_db
def test_no_institution_verification_fields_are_added_into_access_billing_models():
    access_state_fields = {
        field.name for field in InstitutionAccessState._meta.get_fields()
    }

    forbidden_fields = {
        "verification_status",
        "verification_case",
        "human_review_status",
        "ai_screening_result",
    }

    assert access_state_fields.isdisjoint(forbidden_fields)


@pytest.mark.django_db
def test_access_state_remains_separate_from_institution_website_state():
    access_state_fields = {
        field.name for field in InstitutionAccessState._meta.get_fields()
    }

    forbidden_fields = {
        "website_status",
        "institution_website_status",
        "domain_status",
        "template_code",
    }

    assert access_state_fields.isdisjoint(forbidden_fields)


@pytest.mark.django_db
def test_payment_method_reference_never_stores_raw_card_number():
    payment_method_fields = {
        field.name for field in PaymentMethodReference._meta.get_fields()
    }

    forbidden_fields = {
        "card_number",
        "raw_card_number",
        "pan",
        "cvv",
        "security_code",
    }

    assert payment_method_fields.isdisjoint(forbidden_fields)
