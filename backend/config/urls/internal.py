"""Small internal scaffolding routes for early authenticated workflows."""

from django.urls import include, path

urlpatterns = [
    path("", include("apps.institutions.api.urls")),
    path("", include("apps.institution_verification.api.urls")),
]
