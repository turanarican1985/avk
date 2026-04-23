"""Behavior tests for institution verification services."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.institution_verification.models import (
    AIScreeningResultStatus,
    InstitutionVerificationCase,
    VerificationCaseStatus,
    VerificationDecisionType,
    VerificationSubmissionSource,
)
from apps.institution_verification.services import (
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


@pytest.mark.django_db
def test_open_verification_case(institution, institution_user):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
    )

    assert verification_case.institution == institution
    assert verification_case.status == VerificationCaseStatus.DRAFT


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
def test_ai_clean_result_routes_to_human_review_pending(
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
        confidence_score=Decimal("0.4200"),
        summary="No high-confidence fraud signal.",
    )

    route_case_after_ai_screening(
        verification_case=verification_case,
        screening_result=screening_result,
    )

    verification_case.refresh_from_db()
    assert verification_case.status == VerificationCaseStatus.HUMAN_REVIEW_PENDING


@pytest.mark.django_db
def test_ai_high_confidence_rejection_does_not_route_to_human_approval_state_directly(
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
    assert verification_case.status != VerificationCaseStatus.APPROVED


@pytest.mark.django_db
def test_support_linked_reupload_creates_documents_with_support_reupload(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
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

    assert len(documents) == 1
    assert documents[0].upload_source == VerificationSubmissionSource.SUPPORT_REUPLOAD


@pytest.mark.django_db
def test_support_reupload_bypasses_ai_and_routes_to_human_review_pending(
    institution, institution_user, sample_documents
):
    verification_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
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
def test_human_approval_and_rejection_decisions_produce_expected_case_states(
    institution, institution_user
):
    approval_case = open_verification_case(
        institution=institution,
        opened_by=institution_user,
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
