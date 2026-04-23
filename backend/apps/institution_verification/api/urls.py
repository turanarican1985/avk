"""Internal URL routes for institution verification scaffolding."""

from django.urls import path

from apps.institution_verification.api.views import (
    InstitutionVerificationCaseListCreateView,
)

urlpatterns = [
    path(
        "institutions/<uuid:institution_id>/verification-cases/",
        InstitutionVerificationCaseListCreateView.as_view(),
        name="internal-institution-verification-case-list-create",
    ),
]
