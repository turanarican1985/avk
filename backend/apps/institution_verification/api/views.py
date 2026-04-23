"""Minimal internal API views for institution verification."""

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from apps.institution_verification.api.serializers import (
    InstitutionVerificationCaseSerializer,
    OpenVerificationCaseSerializer,
)
from apps.institution_verification.selectors import (
    list_verification_cases_for_institution,
)
from apps.institutions.models import Institution
from apps.institutions.selectors import user_has_institution_membership


class InstitutionVerificationCaseListCreateView(generics.ListCreateAPIView):
    """List or open verification cases for an institution the user can manage."""

    serializer_class = InstitutionVerificationCaseSerializer

    def _get_institution(self) -> Institution:
        institution = get_object_or_404(Institution, id=self.kwargs["institution_id"])
        if self.request.user.is_superuser:
            return institution
        if not user_has_institution_membership(
            institution=institution, user=self.request.user
        ):
            raise PermissionDenied("You do not belong to this institution.")
        return institution

    def get_queryset(self):
        institution = self._get_institution()
        return list_verification_cases_for_institution(institution=institution)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OpenVerificationCaseSerializer
        return InstitutionVerificationCaseSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["institution"] = self._get_institution()
        return context

    def perform_create(self, serializer):
        self.instance = serializer.save()
