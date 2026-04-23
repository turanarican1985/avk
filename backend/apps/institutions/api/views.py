"""Minimal internal API views for institutions."""

from rest_framework import generics

from apps.institutions.api.serializers import (
    CreateInstitutionSerializer,
    InstitutionSerializer,
)
from apps.institutions.selectors import list_institutions_for_user


class InstitutionListCreateView(generics.ListCreateAPIView):
    """List or create institutions for the authenticated user."""

    serializer_class = InstitutionSerializer

    def get_queryset(self):
        return list_institutions_for_user(user=self.request.user).order_by(
            "display_name"
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateInstitutionSerializer
        return InstitutionSerializer

    def perform_create(self, serializer):
        self.instance = serializer.save()
