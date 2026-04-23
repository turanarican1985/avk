"""Behavior tests for the internal institution verification API scaffolding."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.institution_verification.models import VerificationCaseStatus
from apps.institution_verification.services import open_verification_case
from apps.institutions.models import InstitutionType
from apps.institutions.services import attach_owner_membership, create_institution


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def institution_owner():
    return get_user_model().objects.create_user(
        email="institution-owner@example.com",
        password="testpass123",
    )


@pytest.fixture
def institution(institution_owner):
    institution = create_institution(
        legal_name="Zirve Hukuk",
        display_name="Zirve Hukuk",
        slug="zirve-hukuk",
        institution_type=InstitutionType.TEAM_BASED,
    )
    attach_owner_membership(institution=institution, user=institution_owner)
    return institution


@pytest.mark.django_db
def test_institution_member_can_list_verification_cases_for_their_institution(
    api_client, institution_owner, institution
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_owner,
    )

    api_client.force_authenticate(user=institution_owner)
    response = api_client.get(
        reverse(
            "internal-institution-verification-case-list-create",
            kwargs={"institution_id": institution.id},
        )
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(verification_case.id)


@pytest.mark.django_db
def test_non_member_cannot_list_another_institutions_verification_cases(
    api_client, institution
):
    other_user = get_user_model().objects.create_user(
        email="outsider@example.com",
        password="testpass123",
    )

    api_client.force_authenticate(user=other_user)
    response = api_client.get(
        reverse(
            "internal-institution-verification-case-list-create",
            kwargs={"institution_id": institution.id},
        )
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_superuser_can_access_verification_cases_without_membership(
    api_client, institution
):
    superuser = get_user_model().objects.create_superuser(
        email="admin@example.com",
        password="testpass123",
    )
    verification_case = open_verification_case(institution=institution, opened_by=None)

    api_client.force_authenticate(user=superuser)
    response = api_client.get(
        reverse(
            "internal-institution-verification-case-list-create",
            kwargs={"institution_id": institution.id},
        )
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(verification_case.id)


@pytest.mark.django_db
def test_authenticated_member_can_open_verification_case_through_internal_api(
    api_client, institution_owner, institution
):
    api_client.force_authenticate(user=institution_owner)
    response = api_client.post(
        reverse(
            "internal-institution-verification-case-list-create",
            kwargs={"institution_id": institution.id},
        ),
        data={},
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["status"] == VerificationCaseStatus.DRAFT


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_internal_verification_endpoint(
    api_client, institution
):
    response = api_client.get(
        reverse(
            "internal-institution-verification-case-list-create",
            kwargs={"institution_id": institution.id},
        )
    )

    assert response.status_code in {401, 403}
