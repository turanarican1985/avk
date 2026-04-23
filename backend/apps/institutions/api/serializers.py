"""Internal serializers for the institutions domain."""

from rest_framework import serializers

from apps.institutions.models import Institution
from apps.institutions.services import attach_owner_membership, create_institution


class InstitutionSerializer(serializers.ModelSerializer):
    """Representation of an institution for internal scaffolding endpoints."""

    class Meta:
        model = Institution
        fields = [
            "id",
            "legal_name",
            "display_name",
            "slug",
            "institution_type",
            "lifecycle_status",
            "is_publicly_visible",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CreateInstitutionSerializer(serializers.Serializer):
    """Minimal payload for creating an institution in early internal APIs."""

    legal_name = serializers.CharField(max_length=255)
    display_name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=255)
    institution_type = serializers.ChoiceField(
        choices=Institution._meta.get_field("institution_type").choices
    )

    def create(self, validated_data):
        request = self.context["request"]
        institution = create_institution(
            legal_name=validated_data["legal_name"],
            display_name=validated_data["display_name"],
            slug=validated_data["slug"],
            institution_type=validated_data["institution_type"],
            actor_id=str(request.user.id),
        )
        attach_owner_membership(
            institution=institution,
            user=request.user,
            actor_id=str(request.user.id),
        )
        return institution

    def to_representation(self, instance):
        return InstitutionSerializer(instance, context=self.context).data
