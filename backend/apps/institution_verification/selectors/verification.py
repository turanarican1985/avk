"""Read-oriented selectors for institution verification."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.institution_verification.models import (
    InstitutionVerificationCase,
    InstitutionVerificationDocument,
    VerificationCaseStatus,
)
from apps.institutions.models import Institution


def get_verification_case_by_id(*, verification_case_id) -> InstitutionVerificationCase:
    """Return a verification case by its primary key."""

    return InstitutionVerificationCase.objects.get(id=verification_case_id)


def get_active_verification_case_for_institution(
    *, institution: Institution
) -> InstitutionVerificationCase | None:
    """Return the current non-terminal verification case for an institution."""

    return (
        InstitutionVerificationCase.objects.filter(institution=institution)
        .exclude(
            status__in=[
                VerificationCaseStatus.AI_REJECTED_HIGH_CONFIDENCE,
                VerificationCaseStatus.APPROVED,
                VerificationCaseStatus.REJECTED,
            ]
        )
        .order_by("-created_at")
        .first()
    )


def list_verification_cases_for_institution(
    *, institution: Institution
) -> QuerySet[InstitutionVerificationCase]:
    """Return verification cases for an institution."""

    return InstitutionVerificationCase.objects.filter(institution=institution)


def list_documents_for_verification_case(
    *, verification_case: InstitutionVerificationCase
) -> QuerySet[InstitutionVerificationDocument]:
    """Return documents for a verification case."""

    return InstitutionVerificationDocument.objects.filter(
        verification_case=verification_case
    )
