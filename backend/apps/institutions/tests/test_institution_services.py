"""Behavior tests for the institutions domain services."""

import pytest
from django.contrib.auth import get_user_model

from apps.institutions.models import InstitutionMembershipRole, InstitutionType
from apps.institutions.services import (
    attach_owner_membership,
    create_institution,
)


@pytest.mark.django_db
def test_create_solo_institution():
    institution = create_institution(
        legal_name="Avukat Ayse Yilmaz",
        display_name="Avukat Ayse Yilmaz",
        slug="avukat-ayse-yilmaz",
        institution_type=InstitutionType.SOLO,
    )

    assert institution.institution_type == InstitutionType.SOLO
    assert institution.slug == "avukat-ayse-yilmaz"


@pytest.mark.django_db
def test_create_team_based_institution():
    institution = create_institution(
        legal_name="Yilmaz Hukuk Burosu",
        display_name="Yilmaz Hukuk Burosu",
        slug="yilmaz-hukuk-burosu",
        institution_type=InstitutionType.TEAM_BASED,
    )

    assert institution.institution_type == InstitutionType.TEAM_BASED
    assert institution.display_name == "Yilmaz Hukuk Burosu"


@pytest.mark.django_db
def test_attach_owner_membership():
    user = get_user_model().objects.create_user(
        email="owner@example.com",
        password="testpass123",
    )
    institution = create_institution(
        legal_name="Demir Hukuk",
        display_name="Demir Hukuk",
        slug="demir-hukuk",
        institution_type=InstitutionType.TEAM_BASED,
    )

    membership = attach_owner_membership(institution=institution, user=user)

    assert membership.role == InstitutionMembershipRole.OWNER
    assert membership.user == user
    assert membership.institution == institution
    assert membership.is_active is True
