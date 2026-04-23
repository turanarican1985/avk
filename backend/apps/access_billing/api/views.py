"""Minimal internal API views for commercial-access scaffolding."""

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.access_billing.api.serializers import (
    AccessPlanSerializer,
    ChargeScheduleSerializer,
    InstitutionAccessStateSerializer,
    StartInstitutionAccessSerializer,
)
from apps.access_billing.models import ChargeSchedule
from apps.access_billing.selectors import (
    get_access_state_for_institution,
    list_active_plans,
)
from apps.institutions.models import Institution
from apps.institutions.selectors import user_has_institution_membership


class ActiveAccessPlanListView(generics.ListAPIView):
    """List active plans for internal authenticated consumers."""

    serializer_class = AccessPlanSerializer

    def get_queryset(self):
        return list_active_plans()


class InstitutionAccessPermissionMixin:
    """Shared institution access lookup for commercial-access scaffolding APIs."""

    def get_institution(self) -> Institution:
        institution = get_object_or_404(Institution, id=self.kwargs["institution_id"])
        if self.request.user.is_superuser:
            return institution
        if not user_has_institution_membership(
            institution=institution,
            user=self.request.user,
        ):
            raise PermissionDenied("You do not belong to this institution.")
        return institution


class InstitutionAccessStateDetailView(
    InstitutionAccessPermissionMixin,
    generics.RetrieveAPIView,
):
    """Inspect the current commercial-access state for an institution."""

    serializer_class = InstitutionAccessStateSerializer

    def get_object(self):
        access_state = get_access_state_for_institution(
            institution=self.get_institution(),
        )
        if access_state is None:
            raise NotFound(
                "No commercial access state exists for this institution yet."
            )
        return access_state


class InstitutionAccessStartView(
    InstitutionAccessPermissionMixin,
    generics.CreateAPIView,
):
    """Start the one-month full-feature access period for an institution."""

    serializer_class = StartInstitutionAccessSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["institution"] = self.get_institution()
        return context

    def perform_create(self, serializer):
        self.instance = serializer.save()


class InstitutionChargeScheduleListView(
    InstitutionAccessPermissionMixin,
    generics.ListAPIView,
):
    """List charge schedules for an institution."""

    serializer_class = ChargeScheduleSerializer

    def get_queryset(self):
        return ChargeSchedule.objects.select_related(
            "access_state",
            "plan",
            "coupon",
        ).filter(access_state__institution=self.get_institution())
