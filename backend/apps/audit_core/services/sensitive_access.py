"""Sensitive-data access logging abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class SensitiveAccessEvent:
    """Captures who accessed protected data and why the access happened."""

    actor_id: str | None
    actor_role: str
    resource_type: str
    resource_id: str | None
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SensitiveAccessLogger(Protocol):
    """Protocol implemented by later audit sinks with restricted visibility."""

    def log(self, event: SensitiveAccessEvent) -> None:
        """Store or forward a sensitive-access event."""


class NoOpSensitiveAccessLogger:
    """Bootstrap implementation that keeps call sites stable without side effects."""

    def log(self, event: SensitiveAccessEvent) -> None:
        return None


def log_sensitive_access(
    event: SensitiveAccessEvent, logger: SensitiveAccessLogger | None = None
) -> None:
    """Log sensitive-data access through an explicit abstraction."""
    effective_logger = logger or NoOpSensitiveAccessLogger()
    effective_logger.log(event)
