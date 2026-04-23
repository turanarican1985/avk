"""Admin integration for institution verification."""

from django.contrib import admin

from apps.institution_verification.models import (
    InstitutionAIScreeningResult,
    InstitutionVerificationCase,
    InstitutionVerificationDecision,
    InstitutionVerificationDocument,
)


@admin.register(InstitutionVerificationCase)
class InstitutionVerificationCaseAdmin(admin.ModelAdmin):
    """Admin configuration for verification cases."""

    list_display = (
        "reference_code",
        "institution",
        "status",
        "latest_submission_source",
        "support_reupload_allowed",
        "current_submission_ai_bypassed",
        "created_at",
    )
    list_filter = (
        "status",
        "latest_submission_source",
        "support_reupload_allowed",
        "current_submission_ai_bypassed",
    )
    search_fields = ("reference_code", "institution__display_name", "institution__slug")
    readonly_fields = (
        "id",
        "reference_code",
        "submitted_at",
        "last_human_review_routed_at",
        "created_at",
        "updated_at",
    )


@admin.register(InstitutionVerificationDocument)
class InstitutionVerificationDocumentAdmin(admin.ModelAdmin):
    """Admin configuration for verification documents."""

    list_display = (
        "verification_case",
        "document_type",
        "upload_source",
        "original_filename",
        "created_at",
    )
    list_filter = ("document_type", "upload_source")
    search_fields = (
        "verification_case__reference_code",
        "original_filename",
        "file_reference",
    )
    readonly_fields = ("id", "created_at")


@admin.register(InstitutionAIScreeningResult)
class InstitutionAIScreeningResultAdmin(admin.ModelAdmin):
    """Admin configuration for AI screening results."""

    list_display = (
        "verification_case",
        "result_status",
        "confidence_score",
        "created_at",
    )
    list_filter = ("result_status",)
    search_fields = ("verification_case__reference_code", "summary")
    readonly_fields = ("id", "created_at")


@admin.register(InstitutionVerificationDecision)
class InstitutionVerificationDecisionAdmin(admin.ModelAdmin):
    """Admin configuration for human verification decisions."""

    list_display = ("verification_case", "decision_type", "actor", "created_at")
    list_filter = ("decision_type",)
    search_fields = ("verification_case__reference_code", "note", "actor__email")
    readonly_fields = ("id", "created_at")
