"""Behavior tests for institution verification services."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.institution_verification.models import (
    AIScreeningResultStatus,
    InstitutionAIScreeningResult,
    InstitutionVerificationCase,
    VerificationCaseStatus,
    VerificationDecisionType,
    VerificationSubmissionSource,
)
from apps.institution_verification.services import (
    InvalidVerificationTransition,
    create_support_linked_reupload_submission,
    open_verification_case,
    record_ai_screening_result,
    record_human_verification_decision,
    route_case_after_ai_screening,
    submit_verification_documents,
)
from apps.institutions.models import InstitutionType
from apps.institutions.services import attach_owner_membership, create_institution


@pytest.fixture
def institution_user():
    return get_user_model().objects.create_user(
        email="institution@example.com",
        password="testpass123",
    )


@pytest.fixture
def institution(institution_user):
    institution = create_institution(
        legal_name="Kaya Hukuk",
        display_name="Kaya Hukuk",
        slug="kaya-hukuk",
        institution_type=InstitutionType.TEAM_BASED,
    )
    attach_owner_membership(institution=institution, user=institution_user)
    return institution


@pytest.fixture
def sample_documents():
    return [
        {
            "document_type": "bar_registration",
            "file_reference": "verification/kaya/bar.pdf",
            "original_filename": "bar.pdf",
        }
    ]


def move_case_to_human_review_pending(
    *, verification_case, institution_user, sample_documents
):
    """Submit through the normal portal path and route via AI to human review."""

    submit_verification_documents(
        verification_case=verification_case,
        documents=sample_documents,
        uploaded_by=institution_user,
    )
    screening_result = record_ai_screening_result(
        verification_case=verification_case,
        result_status=AIScreeningResultStatus.CLEAN,
        confidence_score=Decimal("0.4200"),
        summary="No high-confidence fraud signal.",
    )
    route_case_after_ai_screening(
        verification_case=verification_case,
        screening_result=screening_result,
    )
    verification_case.refresh_from_db()
    return verification_case


@pytest.mark.django_db
def test_open_verification_case(institution, institution_user):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )

    assert verification_case.institution == institution
    assert verification_case.status == VerificationCaseStatus.DRAFT


@pytest.mark.django_db
def test_opening_new_case_while_active_case_exists_reuses_current_case(
    institution, institution_user
):
    first_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    second_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )

    assert first_case.id == second_case.id
    assert (
        InstitutionVerificationCase.objects.filter(institution=institution).count() == 1
    )


@pytest.mark.django_db
def test_institution_upload_path_creates_documents_with_institution_portal(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )

    documents = submit_verification_documents(
        verification_case=verification_case,
        documents=sample_documents,
        uploaded_by=institution_user,
    )

    assert len(documents) == 1
    assert documents[0].upload_source == VerificationSubmissionSource.INSTITUTION_PORTAL
    verification_case.refresh_from_db()
    assert verification_case.status == VerificationCaseStatus.SUBMITTED


@pytest.mark.django_db
def test_human_decision_from_draft_is_rejected(institution, institution_user):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )

    with pytest.raises(InvalidVerificationTransition):
        record_human_verification_decision(
            verification_case=verification_case,
            decision_type=VerificationDecisionType.APPROVED,
            actor=institution_user,
        )


@pytest.mark.django_db
def test_human_decision_from_submitted_is_rejected(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    submit_verification_documents(
        verification_case=verification_case,
        documents=sample_documents,
        uploaded_by=institution_user,
    )

    with pytest.raises(InvalidVerificationTransition):
        record_human_verification_decision(
            verification_case=verification_case,
            decision_type=VerificationDecisionType.APPROVED,
            actor=institution_user,
        )


@pytest.mark.django_db
def test_human_decision_from_terminal_state_is_rejected(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    move_case_to_human_review_pending(
        verification_case=verification_case,
        institution_user=institution_user,
        sample_documents=sample_documents,
    )
    record_human_verification_decision(
        verification_case=verification_case,
        decision_type=VerificationDecisionType.APPROVED,
        actor=institution_user,
    )

    with pytest.raises(InvalidVerificationTransition):
        record_human_verification_decision(
            verification_case=verification_case,
            decision_type=VerificationDecisionType.REJECTED,
            actor=institution_user,
        )


@pytest.mark.django_db
def test_institution_portal_submission_and_clean_ai_routes_to_human_review_pending(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )

    move_case_to_human_review_pending(
        verification_case=verification_case,
        institution_user=institution_user,
        sample_documents=sample_documents,
    )

    verification_case.refresh_from_db()
    assert verification_case.status == VerificationCaseStatus.HUMAN_REVIEW_PENDING


@pytest.mark.django_db
def test_institution_portal_submission_and_high_confidence_reject_routes_to_ai_rejected(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    submit_verification_documents(
        verification_case=verification_case,
        documents=sample_documents,
        uploaded_by=institution_user,
    )
    screening_result = record_ai_screening_result(
        verification_case=verification_case,
        result_status=AIScreeningResultStatus.REJECTED_HIGH_CONFIDENCE,
        confidence_score=Decimal("0.9900"),
        summary="Strong evidence of tampering.",
        flags=["tampering_detected"],
    )

    route_case_after_ai_screening(
        verification_case=verification_case,
        screening_result=screening_result,
    )

    verification_case.refresh_from_db()
    assert (
        verification_case.status == VerificationCaseStatus.AI_REJECTED_HIGH_CONFIDENCE
    )


@pytest.mark.django_db
def test_ai_never_produces_approved_state(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    submit_verification_documents(
        verification_case=verification_case,
        documents=sample_documents,
        uploaded_by=institution_user,
    )
    screening_result = record_ai_screening_result(
        verification_case=verification_case,
        result_status=AIScreeningResultStatus.CLEAN,
        confidence_score=Decimal("0.5100"),
    )

    route_case_after_ai_screening(
        verification_case=verification_case,
        screening_result=screening_result,
    )

    verification_case.refresh_from_db()
    assert verification_case.status != VerificationCaseStatus.APPROVED


@pytest.mark.django_db
def test_support_linked_reupload_when_not_allowed_is_rejected(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )

    with pytest.raises(InvalidVerificationTransition):
        create_support_linked_reupload_submission(
            verification_case=verification_case,
            documents=sample_documents,
            uploaded_by=institution_user,
        )


@pytest.mark.django_db
def test_correction_requested_reupload_routes_directly_to_human_review_pending(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    move_case_to_human_review_pending(
        verification_case=verification_case,
        institution_user=institution_user,
        sample_documents=sample_documents,
    )
    record_human_verification_decision(
        verification_case=verification_case,
        decision_type=VerificationDecisionType.CORRECTION_REQUESTED,
        actor=institution_user,
        note="Please re-upload a clearer document set.",
    )

    documents = create_support_linked_reupload_submission(
        verification_case=verification_case,
        documents=sample_documents,
        uploaded_by=institution_user,
    )

    verification_case.refresh_from_db()
    assert len(documents) == 1
    assert documents[0].upload_source == VerificationSubmissionSource.SUPPORT_REUPLOAD
    assert verification_case.status == VerificationCaseStatus.HUMAN_REVIEW_PENDING
    assert verification_case.current_submission_ai_bypassed is True
    assert verification_case.support_reupload_allowed is False


@pytest.mark.django_db
def test_rejected_reupload_routes_directly_to_human_review_pending(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    move_case_to_human_review_pending(
        verification_case=verification_case,
        institution_user=institution_user,
        sample_documents=sample_documents,
    )
    record_human_verification_decision(
        verification_case=verification_case,
        decision_type=VerificationDecisionType.REJECTED,
        actor=institution_user,
        note="Please submit corrected proof via support-linked path.",
    )

    create_support_linked_reupload_submission(
        verification_case=verification_case,
        documents=sample_documents,
        uploaded_by=institution_user,
    )

    verification_case.refresh_from_db()
    assert verification_case.status == VerificationCaseStatus.HUMAN_REVIEW_PENDING
    assert verification_case.current_submission_ai_bypassed is True
    assert (
        verification_case.latest_submission_source
        == VerificationSubmissionSource.SUPPORT_REUPLOAD
    )


@pytest.mark.django_db
def test_ai_routing_after_support_linked_reupload_is_rejected(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    move_case_to_human_review_pending(
        verification_case=verification_case,
        institution_user=institution_user,
        sample_documents=sample_documents,
    )
    record_human_verification_decision(
        verification_case=verification_case,
        decision_type=VerificationDecisionType.CORRECTION_REQUESTED,
        actor=institution_user,
    )
    create_support_linked_reupload_submission(
        verification_case=verification_case,
        documents=sample_documents,
        uploaded_by=institution_user,
    )

    with pytest.raises(InvalidVerificationTransition):
        record_ai_screening_result(
            verification_case=verification_case,
            result_status=AIScreeningResultStatus.CLEAN,
            confidence_score=Decimal("0.1000"),
        )


@pytest.mark.django_db
def test_support_reupload_never_invokes_ai_routing_path(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    move_case_to_human_review_pending(
        verification_case=verification_case,
        institution_user=institution_user,
        sample_documents=sample_documents,
    )
    record_human_verification_decision(
        verification_case=verification_case,
        decision_type=VerificationDecisionType.REJECTED,
        actor=institution_user,
    )
    create_support_linked_reupload_submission(
        verification_case=verification_case,
        documents=sample_documents,
        uploaded_by=institution_user,
    )
    screening_result = InstitutionAIScreeningResult.objects.create(
        verification_case=verification_case,
        result_status=AIScreeningResultStatus.CLEAN,
        confidence_score=Decimal("0.1000"),
    )

    with pytest.raises(InvalidVerificationTransition):
        route_case_after_ai_screening(
            verification_case=verification_case,
            screening_result=screening_result,
        )


@pytest.mark.django_db
def test_terminal_case_rejects_new_institution_portal_submission(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    move_case_to_human_review_pending(
        verification_case=verification_case,
        institution_user=institution_user,
        sample_documents=sample_documents,
    )
    record_human_verification_decision(
        verification_case=verification_case,
        decision_type=VerificationDecisionType.APPROVED,
        actor=institution_user,
    )

    with pytest.raises(InvalidVerificationTransition):
        submit_verification_documents(
            verification_case=verification_case,
            documents=sample_documents,
            uploaded_by=institution_user,
        )


@pytest.mark.django_db
def test_human_approval_and_rejection_decisions_produce_expected_case_states(
    institution, institution_user, sample_documents
):
    approval_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )
    move_case_to_human_review_pending(
        verification_case=approval_case,
        institution_user=institution_user,
        sample_documents=sample_documents,
    )
    record_human_verification_decision(
        verification_case=approval_case,
        decision_type=VerificationDecisionType.APPROVED,
        actor=institution_user,
        note="Approved after manual review.",
    )
    approval_case.refresh_from_db()

    rejected_case = InstitutionVerificationCase.objects.create(
        institution=institution,
        opened_by=institution_user,
        status=VerificationCaseStatus.HUMAN_REVIEW_PENDING,
    )
    record_human_verification_decision(
        verification_case=rejected_case,
        decision_type=VerificationDecisionType.REJECTED,
        actor=institution_user,
        note="Rejected after manual review.",
    )
    rejected_case.refresh_from_db()

    assert approval_case.status == VerificationCaseStatus.APPROVED
    assert rejected_case.status == VerificationCaseStatus.REJECTED
    assert rejected_case.support_reupload_allowed is True


@pytest.mark.django_db
def test_verification_models_do_not_include_billing_fields():
    verification_fields = {
        field.name for field in InstitutionVerificationCase._meta.get_fields()
    }

    forbidden_fields = {
        "trial_access_status",
        "commercial_access_status",
        "subscription_status",
        "card_token",
        "charge_scheduled_at",
        "plan_period",
        "coupon_code",
    }

    assert verification_fields.isdisjoint(forbidden_fields)
