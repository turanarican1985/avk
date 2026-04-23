"""Write-oriented institution services."""

from __future__ import annotations

from django.db import transaction

from apps.audit_core.services.recorder import AuditActor, AuditEvent, record_audit_event
from apps.institutions.models import (
    Institution,
    InstitutionLifecycleStatus,
    InstitutionMembership,
    InstitutionMembershipRole,
    InstitutionType,
)


@transaction.atomic
def create_institution(
    *,
    legal_name: str,
    display_name: str,
    slug: str,
    institution_type: InstitutionType | str,
    actor_id: str | None = None,
) -> Institution:
    """Create the shared institution entity."""

    institution = Institution.objects.create(
        legal_name=legal_name,
        display_name=display_name,
        slug=slug,
        institution_type=institution_type,
        lifecycle_status=InstitutionLifecycleStatus.DRAFT,
    )
    record_audit_event(
        AuditEvent(
            event_name="institutions.institution_created",
            actor=(
                AuditActor(actor_id=actor_id, actor_type="user") if actor_id else None
            ),
            target_type="institution",
            target_id=str(institution.id),
            metadata={"institution_type": institution.institution_type},
        )
    )
    return institution


@transaction.atomic
def attach_institution_membership(
    *,
    institution: Institution,
    user,
    role: InstitutionMembershipRole | str,
    actor_id: str | None = None,
) -> InstitutionMembership:
    """Attach or update a user membership for an institution."""

    membership, created = InstitutionMembership.objects.get_or_create(
        institution=institution,
        user=user,
        defaults={"role": role, "is_active": True},
    )
    if not created:
        membership.role = role
        membership.is_active = True
        membership.save(update_fields=["role", "is_active", "updated_at"])

    record_audit_event(
        AuditEvent(
            event_name="institutions.membership_attached",
            actor=(
                AuditActor(actor_id=actor_id, actor_type="user") if actor_id else None
            ),
            target_type="institution_membership",
            target_id=str(membership.id),
            metadata={
                "institution_id": str(institution.id),
                "user_id": str(user.id),
                "role": membership.role,
            },
        )
    )
    return membership


def attach_owner_membership(
    *, institution: Institution, user, actor_id: str | None = None
):
    """Convenience wrapper for the common institution owner relationship."""

    return attach_institution_membership(
        institution=institution,
        user=user,
        role=InstitutionMembershipRole.OWNER,
        actor_id=actor_id,
    )
