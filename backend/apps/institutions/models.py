"""Core institution models."""

from __future__ import annotations

from uuid import uuid4

from django.conf import settings
from django.db import models


class InstitutionType(models.TextChoices):
    """Supported institution presentation modes."""

    SOLO = "solo", "Solo"
    TEAM_BASED = "team_based", "Team Based"


class InstitutionLifecycleStatus(models.TextChoices):
    """Lifecycle states for early institution management."""

    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class InstitutionMembershipRole(models.TextChoices):
    """Roles for institution-associated users."""

    OWNER = "owner", "Owner"
    MANAGER = "manager", "Manager"
    EDITOR = "editor", "Editor"


class Institution(models.Model):
    """Shared institution entity for both solo and team-based organizations."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    legal_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    institution_type = models.CharField(max_length=20, choices=InstitutionType.choices)
    lifecycle_status = models.CharField(
        max_length=20,
        choices=InstitutionLifecycleStatus.choices,
        default=InstitutionLifecycleStatus.DRAFT,
    )
    is_publicly_visible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name", "legal_name"]

    def __str__(self) -> str:
        return self.display_name


class InstitutionMembership(models.Model):
    """Relationship between a user and an institution."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="institution_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=InstitutionMembershipRole.choices,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["institution__display_name", "user__email"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "user"],
                name="unique_institution_membership",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.institution} ({self.role})"
