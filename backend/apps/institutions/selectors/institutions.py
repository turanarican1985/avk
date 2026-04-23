"""Read-oriented institution selectors."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.institutions.models import Institution, InstitutionMembership


def get_institution_by_id(*, institution_id) -> Institution:
    """Return an institution by its primary key."""

    return Institution.objects.get(id=institution_id)


def get_institution_by_slug(*, slug: str) -> Institution:
    """Return an institution by its public slug."""

    return Institution.objects.get(slug=slug)


def list_memberships_for_institution(
    *, institution: Institution
) -> QuerySet[InstitutionMembership]:
    """Return active memberships for a given institution."""

    return InstitutionMembership.objects.filter(institution=institution, is_active=True)


def list_institutions_for_user(*, user) -> QuerySet[Institution]:
    """Return institutions linked to a specific user."""

    return Institution.objects.filter(
        memberships__user=user, memberships__is_active=True
    ).distinct()


def user_has_institution_membership(*, institution: Institution, user) -> bool:
    """Check whether a user is actively attached to an institution."""

    return InstitutionMembership.objects.filter(
        institution=institution,
        user=user,
        is_active=True,
    ).exists()
