"""Internal URL routes for institution scaffolding."""

from django.urls import path

from apps.institutions.api.views import InstitutionListCreateView

urlpatterns = [
    path(
        "institutions/",
        InstitutionListCreateView.as_view(),
        name="internal-institution-list-create",
    ),
]
