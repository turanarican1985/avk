"""Permission abstractions for scoped staff operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class StaffActor:
    """Represents the acting staff member in authorization checks."""

    actor_id: str | None
    role_codes: tuple[str, ...] = ()
    team_codes: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PermissionDecision:
    """Normalized permission-check response used by future services and APIs."""

    allowed: bool
    reason: str


class PermissionBackend(Protocol):
    """Protocol for pluggable permission engines."""

    def has_permission(
        self,
        *,
        actor: StaffActor,
        permission_code: str,
        context: dict[str, Any] | None = None,
    ) -> PermissionDecision:
        """Evaluate whether the actor may perform the requested action."""


class DenyByDefaultPermissionBackend:
    """Conservative fallback until the real permission matrix is modeled."""

    def has_permission(
        self,
        *,
        actor: StaffActor,
        permission_code: str,
        context: dict[str, Any] | None = None,
    ) -> PermissionDecision:
        return PermissionDecision(
            allowed=False,
            reason=f"Permission '{permission_code}' is not configured in Phase 0.",
        )


def check_permission(
    *,
    actor: StaffActor,
    permission_code: str,
    backend: PermissionBackend | None = None,
    context: dict[str, Any] | None = None,
) -> PermissionDecision:
    """Run a permission check through an explicit backend boundary."""
    effective_backend = backend or DenyByDefaultPermissionBackend()
    return effective_backend.has_permission(
        actor=actor,
        permission_code=permission_code,
        context=context,
    )
