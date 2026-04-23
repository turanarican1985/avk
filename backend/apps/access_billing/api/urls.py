"""Internal URL routes for commercial-access scaffolding."""

from django.urls import path

from apps.access_billing.api.views import (
    ActiveAccessPlanListView,
    InstitutionAccessStartView,
    InstitutionAccessStateDetailView,
    InstitutionChargeScheduleListView,
)

urlpatterns = [
    path(
        "access/plans/",
        ActiveAccessPlanListView.as_view(),
        name="internal-access-plan-list",
    ),
    path(
        "institutions/<uuid:institution_id>/access-state/",
        InstitutionAccessStateDetailView.as_view(),
        name="internal-institution-access-state-detail",
    ),
    path(
        "institutions/<uuid:institution_id>/access-state/start/",
        InstitutionAccessStartView.as_view(),
        name="internal-institution-access-start",
    ),
    path(
        "institutions/<uuid:institution_id>/charge-schedules/",
        InstitutionChargeScheduleListView.as_view(),
        name="internal-institution-charge-schedule-list",
    ),
]
