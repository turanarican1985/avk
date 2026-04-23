"""Internal serializers for institution verification scaffolding."""

from rest_framework import serializers

from apps.institution_verification.models import InstitutionVerificationCase
from apps.institution_verification.services import open_verification_case


class InstitutionVerificationCaseSerializer(serializers.ModelSerializer):
    """Representation of verification cases for internal inspection."""

    class Meta:
        model = InstitutionVerificationCase
        fields = [
            "id",
            "reference_code",
            "institution",
            "status",
            "latest_submission_source",
            "support_reupload_allowed",
            "current_submission_ai_bypassed",
            "submitted_at",
            "last_human_review_routed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OpenVerificationCaseSerializer(serializers.Serializer):
    """Minimal payload for opening a verification case."""

    def create(self, validated_data):
        institution = self.context["institution"]
        request = self.context["request"]
        return open_verification_case(institution=institution, opened_by=request.user)

    def to_representation(self, instance):
        return InstitutionVerificationCaseSerializer(
            instance, context=self.context
        ).data
