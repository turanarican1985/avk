"""Minimal operational API views for Phase 0."""

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Expose a lightweight endpoint for uptime and CI smoke checks."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class ServiceInfoView(APIView):
    """Expose non-sensitive runtime metadata for operators and CI."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "service": "avk-backend",
                "phase": "phase-0",
                "language_code": settings.LANGUAGE_CODE,
                "time_zone": settings.TIME_ZONE,
                "version": settings.APP_VERSION,
            }
        )
