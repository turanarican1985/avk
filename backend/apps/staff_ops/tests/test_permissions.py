"""Smoke tests for the Phase 0 permission abstraction."""

from apps.staff_ops.services.permissions import StaffActor, check_permission


def test_default_permission_backend_denies_access():
    actor = StaffActor(
        actor_id="staff-1",
        role_codes=("support_agent",),
        team_codes=("frontline_support",),
    )

    decision = check_permission(
        actor=actor,
        permission_code="reviews.view_sensitive_contact_data",
    )

    assert decision.allowed is False
    assert "not configured" in decision.reason
