"""Behavior tests for the internal commercial-access API scaffolding."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.access_billing.services import (
    create_access_plan,
    start_full_feature_access_period,
)
from apps.institution_verification.models import (
    InstitutionVerificationCase,
    VerificationCaseStatus,
)
from apps.institutions.models import InstitutionType
from apps.institutions.services import attach_owner_membership, create_institution


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def institution_owner():
    return get_user_model().objects.create_user(
        email="access-owner@example.com",
        password="testpass123",
    )


@pytest.fixture
def outsider_user():
    return get_user_model().objects.create_user(
        email="access-outsider@example.com",
        password="testpass123",
    )


@pytest.fixture
def superuser():
    return get_user_model().objects.create_superuser(
        email="access-admin@example.com",
        password="testpass123",
    )


@pytest.fixture
def institution(institution_owner):
    institution = create_institution(
        legal_name="Gunes Hukuk",
        display_name="Gunes Hukuk",
        slug="gunes-hukuk",
        institution_type=InstitutionType.TEAM_BASED,
    )
    attach_owner_membership(institution=institution, user=institution_owner)
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
        code="api-1m",
        name="API 1 Month",
        duration_months=1,
        base_price_amount=Decimal("1000.00"),
        currency="TRY",
    )


@pytest.fixture
def payment_method_payload():
    return {
        "provider_name": "mockpay",
        "provider_customer_reference": "cust-api-123",
        "provider_payment_method_reference": "pm-api-123",
        "masked_display": "**** **** **** 4242",
        "card_brand": "Visa",
        "expiry_month": 12,
        "expiry_year": 2030,
    }


@pytest.mark.django_db
def test_authenticated_user_can_list_active_plans(api_client, institution_owner):
    active_plan = create_access_plan(
        code="active-1m",
        name="Active Plan",
        duration_months=1,
        base_price_amount=Decimal("1000.00"),
        currency="TRY",
    )
    create_access_plan(
        code="inactive-3m",
        name="Inactive Plan",
        duration_months=3,
        base_price_amount=Decimal("2500.00"),
        currency="TRY",
        is_active=False,
    )

    api_client.force_authenticate(user=institution_owner)
    response = api_client.get(reverse("internal-access-plan-list"))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(active_plan.id)


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_internal_plans_endpoint(api_client):
    response = api_client.get(reverse("internal-access-plan-list"))

    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_institution_member_can_view_their_institution_access_state(
    api_client,
    institution_owner,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    api_client.force_authenticate(user=institution_owner)
    response = api_client.get(
        reverse(
            "internal-institution-access-state-detail",
            kwargs={"institution_id": approved_institution.id},
        )
    )

    assert response.status_code == 200
    assert response.json()["institution"] == str(approved_institution.id)


@pytest.mark.django_db
def test_non_member_cannot_view_another_institutions_access_state(
    api_client,
    outsider_user,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    api_client.force_authenticate(user=outsider_user)
    response = api_client.get(
        reverse(
            "internal-institution-access-state-detail",
            kwargs={"institution_id": approved_institution.id},
        )
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_superuser_can_view_access_state_without_membership(
    api_client,
    superuser,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    api_client.force_authenticate(user=superuser)
    response = api_client.get(
        reverse(
            "internal-institution-access-state-detail",
            kwargs={"institution_id": approved_institution.id},
        )
    )

    assert response.status_code == 200
    assert response.json()["institution"] == str(approved_institution.id)


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_access_state_detail_endpoint(
    api_client,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    response = api_client.get(
        reverse(
            "internal-institution-access-state-detail",
            kwargs={"institution_id": approved_institution.id},
        )
    )

    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_institution_member_can_start_access_for_their_own_institution(
    api_client,
    institution_owner,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    api_client.force_authenticate(user=institution_owner)
    response = api_client.post(
        reverse(
            "internal-institution-access-start",
            kwargs={"institution_id": approved_institution.id},
        ),
        data={
            "plan_id": str(one_month_plan.id),
            "payment_method": payment_method_payload,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["current_state"] == "access_active"


@pytest.mark.django_db
def test_non_member_cannot_start_access_for_another_institution(
    api_client,
    outsider_user,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    api_client.force_authenticate(user=outsider_user)
    response = api_client.post(
        reverse(
            "internal-institution-access-start",
            kwargs={"institution_id": approved_institution.id},
        ),
        data={
            "plan_id": str(one_month_plan.id),
            "payment_method": payment_method_payload,
        },
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_access_start_endpoint(
    api_client,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    response = api_client.post(
        reverse(
            "internal-institution-access-start",
            kwargs={"institution_id": approved_institution.id},
        ),
        data={
            "plan_id": str(one_month_plan.id),
            "payment_method": payment_method_payload,
        },
        format="json",
    )

    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_institution_member_can_list_their_institution_charge_schedules(
    api_client,
    institution_owner,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    api_client.force_authenticate(user=institution_owner)
    response = api_client.get(
        reverse(
            "internal-institution-charge-schedule-list",
            kwargs={"institution_id": approved_institution.id},
        )
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["plan_code"] == one_month_plan.code


@pytest.mark.django_db
def test_non_member_cannot_list_another_institutions_charge_schedules(
    api_client,
    outsider_user,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    api_client.force_authenticate(user=outsider_user)
    response = api_client.get(
        reverse(
            "internal-institution-charge-schedule-list",
            kwargs={"institution_id": approved_institution.id},
        )
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_superuser_can_access_charge_schedules_without_membership(
    api_client,
    superuser,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    api_client.force_authenticate(user=superuser)
    response = api_client.get(
        reverse(
            "internal-institution-charge-schedule-list",
            kwargs={"institution_id": approved_institution.id},
        )
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_charge_schedule_list_endpoint(
    api_client,
    approved_institution,
    one_month_plan,
    payment_method_payload,
):
    start_full_feature_access_period(
        institution=approved_institution,
        plan=one_month_plan,
        payment_method_payload=payment_method_payload,
    )

    response = api_client.get(
        reverse(
            "internal-institution-charge-schedule-list",
            kwargs={"institution_id": approved_institution.id},
        )
    )

    assert response.status_code in {401, 403}
