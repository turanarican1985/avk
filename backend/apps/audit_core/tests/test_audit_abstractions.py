"""Smoke tests for the Phase 0 audit abstractions."""

from apps.audit_core.services.recorder import (
    AuditActor,
    AuditEvent,
    record_audit_event,
)
from apps.audit_core.services.sensitive_access import (
    SensitiveAccessEvent,
    log_sensitive_access,
)


def test_record_audit_event_with_default_recorder_does_not_crash():
    event = AuditEvent(
        event_name="phase0.test_event_recorded",
        actor=AuditActor(actor_id="staff-1", actor_type="staff"),
        target_type="institution",
        target_id="inst-1",
    )

    record_audit_event(event)


def test_log_sensitive_access_with_default_logger_does_not_crash():
    event = SensitiveAccessEvent(
        actor_id="moderator-1",
        actor_role="moderator",
        resource_type="reviewer_contact",
        resource_id="review-1",
        reason="phase-0 smoke test",
    )

    log_sensitive_access(event)
