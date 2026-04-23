"""Institution verification domain models."""

from __future__ import annotations

from uuid import uuid4

from django.conf import settings
from django.db import models

from apps.institutions.models import Institution


def generate_verification_reference() -> str:
    """Generate a human-friendly reference for operational tracing."""

    return f"IVC-{uuid4().hex[:12].upper()}"


class VerificationCaseStatus(models.TextChoices):
    """Lifecycle states for institution verification only."""

    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    HUMAN_REVIEW_PENDING = "human_review_pending", "Human Review Pending"
    AI_REJECTED_HIGH_CONFIDENCE = (
        "ai_rejected_high_confidence",
        "AI Rejected High Confidence",
    )
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CORRECTION_REQUESTED = "correction_requested", "Correction Requested"


class VerificationSubmissionSource(models.TextChoices):
    """Sources that may submit verification evidence."""

    INSTITUTION_PORTAL = "institution_portal", "Institution Portal"
    SUPPORT_REUPLOAD = "support_reupload", "Support Re-upload"


class VerificationDocumentType(models.TextChoices):
    """Supported verification document categories."""

    BAR_REGISTRATION = "bar_registration", "Bar Registration"
    AUTHORIZATION = "authorization", "Authorization"
    TAX_DOCUMENT = "tax_document", "Tax Document"
    IDENTITY = "identity", "Identity"
    OTHER = "other", "Other"


class AIScreeningResultStatus(models.TextChoices):
    """AI routing outcomes for verification submissions."""

    CLEAN = "clean", "Clean"
    FLAGGED_FOR_HUMAN_REVIEW = "flagged_for_human_review", "Flagged For Human Review"
    REJECTED_HIGH_CONFIDENCE = (
        "rejected_high_confidence",
        "Rejected High Confidence",
    )


class VerificationDecisionType(models.TextChoices):
    """Human decision outcomes for verification review."""

    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CORRECTION_REQUESTED = "correction_requested", "Correction Requested"


class InstitutionVerificationCase(models.Model):
    """Verification attempt for an institution."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference_code = models.CharField(
        max_length=20,
        unique=True,
        default=generate_verification_reference,
        editable=False,
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="verification_cases",
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opened_institution_verification_cases",
    )
    status = models.CharField(
        max_length=40,
        choices=VerificationCaseStatus.choices,
        default=VerificationCaseStatus.DRAFT,
    )
    latest_submission_source = models.CharField(
        max_length=32,
        choices=VerificationSubmissionSource.choices,
        default=VerificationSubmissionSource.INSTITUTION_PORTAL,
    )
    support_reupload_allowed = models.BooleanField(default=False)
    current_submission_ai_bypassed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    last_human_review_routed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.reference_code} ({self.institution})"


class InstitutionVerificationDocument(models.Model):
    """Evidence uploaded for a verification case."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    verification_case = models.ForeignKey(
        InstitutionVerificationCase,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(
        max_length=40,
        choices=VerificationDocumentType.choices,
    )
    file_reference = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=255)
    upload_source = models.CharField(
        max_length=32,
        choices=VerificationSubmissionSource.choices,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_institution_verification_documents",
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.verification_case.reference_code} - {self.document_type}"


class InstitutionAIScreeningResult(models.Model):
    """AI pre-screen output for a verification submission."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    verification_case = models.ForeignKey(
        InstitutionVerificationCase,
        on_delete=models.CASCADE,
        related_name="ai_screening_results",
    )
    result_status = models.CharField(
        max_length=40,
        choices=AIScreeningResultStatus.choices,
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
    )
    summary = models.TextField(blank=True)
    flags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.verification_case.reference_code} - {self.result_status}"


class InstitutionVerificationDecision(models.Model):
    """Human verification decision history."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    verification_case = models.ForeignKey(
        InstitutionVerificationCase,
        on_delete=models.CASCADE,
        related_name="decisions",
    )
    decision_type = models.CharField(
        max_length=32,
        choices=VerificationDecisionType.choices,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="institution_verification_decisions",
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.verification_case.reference_code} - {self.decision_type}"
