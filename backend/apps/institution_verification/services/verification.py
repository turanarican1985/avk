"""Write-oriented institution verification services."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit_core.services.recorder import AuditActor, AuditEvent, record_audit_event
from apps.institution_verification.models import (
    AIScreeningResultStatus,
    InstitutionAIScreeningResult,
    InstitutionVerificationCase,
    InstitutionVerificationDecision,
    InstitutionVerificationDocument,
    VerificationCaseStatus,
    VerificationDecisionType,
    VerificationSubmissionSource,
)
from apps.institution_verification.selectors import (
    get_active_verification_case_for_institution,
)
from apps.institutions.models import Institution

HIGH_CONFIDENCE_AI_REJECTION_THRESHOLD = Decimal("0.9500")
TERMINAL_VERIFICATION_CASE_STATUSES = {
    VerificationCaseStatus.AI_REJECTED_HIGH_CONFIDENCE,
    VerificationCaseStatus.APPROVED,
    VerificationCaseStatus.REJECTED,
}


@transaction.atomic
def open_verification_case(
    *,
    institution: Institution,
    opened_by=None,
) -> InstitutionVerificationCase:
    """Open a verification case or reuse the existing active one."""

    active_case = get_active_verification_case_for_institution(institution=institution)
    if active_case is not None:
        return active_case

    verification_case = InstitutionVerificationCase.objects.create(
        institution=institution,
        opened_by=opened_by,
        status=VerificationCaseStatus.DRAFT,
    )
    record_audit_event(
        AuditEvent(
            event_name="institution_verification.case_opened",
            actor=(
                AuditActor(actor_id=str(opened_by.id), actor_type="user")
                if opened_by is not None
                else None
            ),
            target_type="institution_verification_case",
            target_id=str(verification_case.id),
            metadata={"institution_id": str(institution.id)},
        )
    )
    return verification_case


@transaction.atomic
def submit_verification_documents(
    *,
    verification_case: InstitutionVerificationCase,
    documents: list[dict],
    uploaded_by=None,
    upload_source: (
        VerificationSubmissionSource | str
    ) = VerificationSubmissionSource.INSTITUTION_PORTAL,
) -> list[InstitutionVerificationDocument]:
    """Attach uploaded verification documents to a case."""

    created_documents = [
        InstitutionVerificationDocument.objects.create(
            verification_case=verification_case,
            document_type=document["document_type"],
            file_reference=document["file_reference"],
            original_filename=document["original_filename"],
            upload_source=upload_source,
            uploaded_by=uploaded_by,
            metadata=document.get("metadata", {}),
        )
        for document in documents
    ]
    verification_case.latest_submission_source = upload_source
    verification_case.current_submission_ai_bypassed = (
        upload_source == VerificationSubmissionSource.SUPPORT_REUPLOAD
    )
    verification_case.submitted_at = timezone.now()
    verification_case.status = VerificationCaseStatus.SUBMITTED
    verification_case.save(
        update_fields=[
            "latest_submission_source",
            "current_submission_ai_bypassed",
            "submitted_at",
            "status",
            "updated_at",
        ]
    )
    record_audit_event(
        AuditEvent(
            event_name="institution_verification.documents_submitted",
            actor=(
                AuditActor(actor_id=str(uploaded_by.id), actor_type="user")
                if uploaded_by is not None
                else None
            ),
            target_type="institution_verification_case",
            target_id=str(verification_case.id),
            metadata={
                "document_count": len(created_documents),
                "upload_source": upload_source,
            },
        )
    )
    return created_documents


@transaction.atomic
def record_ai_screening_result(
    *,
    verification_case: InstitutionVerificationCase,
    result_status: AIScreeningResultStatus | str,
    confidence_score: Decimal | float | str | None,
    summary: str = "",
    flags: list[str] | None = None,
) -> InstitutionAIScreeningResult:
    """Store AI screening output for a verification case."""

    screening_result = InstitutionAIScreeningResult.objects.create(
        verification_case=verification_case,
        result_status=result_status,
        confidence_score=confidence_score,
        summary=summary,
        flags=flags or [],
    )
    record_audit_event(
        AuditEvent(
            event_name="institution_verification.ai_result_recorded",
            actor=None,
            target_type="institution_ai_screening_result",
            target_id=str(screening_result.id),
            metadata={
                "verification_case_id": str(verification_case.id),
                "result_status": screening_result.result_status,
            },
        )
    )
    return screening_result


@transaction.atomic
def route_case_after_ai_screening(
    *,
    verification_case: InstitutionVerificationCase,
    screening_result: InstitutionAIScreeningResult,
) -> InstitutionVerificationCase:
    """Route a case after AI screening while preserving human approval boundaries."""

    if (
        screening_result.result_status
        == AIScreeningResultStatus.REJECTED_HIGH_CONFIDENCE
        and screening_result.confidence_score is not None
        and screening_result.confidence_score >= HIGH_CONFIDENCE_AI_REJECTION_THRESHOLD
    ):
        verification_case.status = VerificationCaseStatus.AI_REJECTED_HIGH_CONFIDENCE
    else:
        verification_case.status = VerificationCaseStatus.HUMAN_REVIEW_PENDING
        verification_case.last_human_review_routed_at = timezone.now()

    verification_case.current_submission_ai_bypassed = False
    verification_case.save(
        update_fields=[
            "status",
            "last_human_review_routed_at",
            "current_submission_ai_bypassed",
            "updated_at",
        ]
    )
    record_audit_event(
        AuditEvent(
            event_name="institution_verification.case_routed_after_ai",
            actor=None,
            target_type="institution_verification_case",
            target_id=str(verification_case.id),
            metadata={
                "screening_result_id": str(screening_result.id),
                "new_status": verification_case.status,
            },
        )
    )
    return verification_case


@transaction.atomic
def record_human_verification_decision(
    *,
    verification_case: InstitutionVerificationCase,
    decision_type: VerificationDecisionType | str,
    actor=None,
    note: str = "",
) -> InstitutionVerificationDecision:
    """Record a human decision and update the current verification case status."""

    decision = InstitutionVerificationDecision.objects.create(
        verification_case=verification_case,
        decision_type=decision_type,
        actor=actor,
        note=note,
    )

    status_map = {
        VerificationDecisionType.APPROVED: VerificationCaseStatus.APPROVED,
        VerificationDecisionType.REJECTED: VerificationCaseStatus.REJECTED,
        VerificationDecisionType.CORRECTION_REQUESTED: (
            VerificationCaseStatus.CORRECTION_REQUESTED
        ),
    }
    verification_case.status = status_map[decision_type]
    verification_case.support_reupload_allowed = decision_type in {
        VerificationDecisionType.REJECTED,
        VerificationDecisionType.CORRECTION_REQUESTED,
    }
    verification_case.current_submission_ai_bypassed = False
    verification_case.save(
        update_fields=[
            "status",
            "support_reupload_allowed",
            "current_submission_ai_bypassed",
            "updated_at",
        ]
    )
    record_audit_event(
        AuditEvent(
            event_name="institution_verification.human_decision_recorded",
            actor=(
                AuditActor(actor_id=str(actor.id), actor_type="user")
                if actor is not None
                else None
            ),
            target_type="institution_verification_decision",
            target_id=str(decision.id),
            metadata={
                "verification_case_id": str(verification_case.id),
                "decision_type": decision.decision_type,
            },
        )
    )
    return decision


@transaction.atomic
def create_support_linked_reupload_submission(
    *,
    verification_case: InstitutionVerificationCase,
    documents: list[dict],
    uploaded_by=None,
) -> list[InstitutionVerificationDocument]:
    """Submit a support-linked re-upload that bypasses AI and goes to human review."""

    if not verification_case.support_reupload_allowed:
        raise ValueError(
            "This verification case is not eligible for support-linked re-upload."
        )

    created_documents = submit_verification_documents(
        verification_case=verification_case,
        documents=documents,
        uploaded_by=uploaded_by,
        upload_source=VerificationSubmissionSource.SUPPORT_REUPLOAD,
    )
    verification_case.status = VerificationCaseStatus.HUMAN_REVIEW_PENDING
    verification_case.current_submission_ai_bypassed = True
    verification_case.support_reupload_allowed = False
    verification_case.last_human_review_routed_at = timezone.now()
    verification_case.save(
        update_fields=[
            "status",
            "current_submission_ai_bypassed",
            "support_reupload_allowed",
            "last_human_review_routed_at",
            "updated_at",
        ]
    )
    record_audit_event(
        AuditEvent(
            event_name="institution_verification.support_reupload_submitted",
            actor=(
                AuditActor(actor_id=str(uploaded_by.id), actor_type="user")
                if uploaded_by is not None
                else None
            ),
            target_type="institution_verification_case",
            target_id=str(verification_case.id),
            metadata={"document_count": len(created_documents)},
        )
    )
    return created_documents
