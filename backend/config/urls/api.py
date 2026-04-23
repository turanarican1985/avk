"""API routes that are intentionally minimal in Phase 0."""

from django.urls import path

from apps.common.api.views import HealthCheckView, ServiceInfoView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("info/", ServiceInfoView.as_view(), name="service-info"),
]
