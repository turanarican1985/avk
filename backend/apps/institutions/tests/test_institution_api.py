"""Behavior tests for the internal institutions API scaffolding."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.institutions.models import (
    InstitutionMembership,
    InstitutionMembershipRole,
    InstitutionType,
)
from apps.institutions.services import attach_owner_membership, create_institution


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def institution_user():
    return get_user_model().objects.create_user(
        email="owner@example.com",
        password="testpass123",
    )


@pytest.mark.django_db
def test_authenticated_user_can_list_only_their_own_institutions(
    api_client, institution_user
):
    other_user = get_user_model().objects.create_user(
        email="other@example.com",
        password="testpass123",
    )
    own_institution = create_institution(
        legal_name="Aksoy Hukuk",
        display_name="Aksoy Hukuk",
        slug="aksoy-hukuk",
        institution_type=InstitutionType.SOLO,
    )
    other_institution = create_institution(
        legal_name="Diger Hukuk",
        display_name="Diger Hukuk",
        slug="diger-hukuk",
        institution_type=InstitutionType.TEAM_BASED,
    )
    attach_owner_membership(institution=own_institution, user=institution_user)
    attach_owner_membership(institution=other_institution, user=other_user)

    api_client.force_authenticate(user=institution_user)
    response = api_client.get(reverse("internal-institution-list-create"))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(own_institution.id)


@pytest.mark.django_db
def test_authenticated_user_can_create_institution_and_becomes_owner(
    api_client, institution_user
):
    api_client.force_authenticate(user=institution_user)

    response = api_client.post(
        reverse("internal-institution-list-create"),
        data={
            "legal_name": "Yildiz Hukuk",
            "display_name": "Yildiz Hukuk",
            "slug": "yildiz-hukuk",
            "institution_type": InstitutionType.TEAM_BASED,
        },
        format="json",
    )

    assert response.status_code == 201
    membership = InstitutionMembership.objects.get(
        institution_id=response.json()["id"],
        user=institution_user,
    )
    assert membership.role == InstitutionMembershipRole.OWNER


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_internal_institution_endpoint(api_client):
    response = api_client.get(reverse("internal-institution-list-create"))

    assert response.status_code in {401, 403}
