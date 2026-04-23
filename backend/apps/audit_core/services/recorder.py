"""Audit recording abstractions used by future domain services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class AuditActor:
    """Represents the initiating actor for an auditable action."""

    actor_id: str | None
    actor_type: str


@dataclass(slots=True)
class AuditEvent:
    """A normalized audit event payload for future persistence backends."""

    event_name: str
    actor: AuditActor | None
    target_type: str
    target_id: str | None
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditRecorder(Protocol):
    """Protocol implemented by concrete audit sinks in later phases."""

    def record(self, event: AuditEvent) -> None:
        """Persist or dispatch an audit event."""


class NoOpAuditRecorder:
    """Safe default used until the real audit pipeline is introduced."""

    def record(self, event: AuditEvent) -> None:
        return None


def record_audit_event(
    event: AuditEvent,
    recorder: AuditRecorder | None = None,
) -> None:
    """Record an audit event through the configured recorder abstraction."""
    effective_recorder = recorder or NoOpAuditRecorder()
    effective_recorder.record(event)
