"""Admin integration for institutions."""

from django.contrib import admin

from apps.institutions.models import Institution, InstitutionMembership


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    """Admin configuration for inspecting institutions."""

    list_display = (
        "display_name",
        "legal_name",
        "institution_type",
        "lifecycle_status",
        "is_publicly_visible",
        "created_at",
    )
    list_filter = ("institution_type", "lifecycle_status", "is_publicly_visible")
    search_fields = ("display_name", "legal_name", "slug")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(InstitutionMembership)
class InstitutionMembershipAdmin(admin.ModelAdmin):
    """Admin configuration for inspecting institution memberships."""

    list_display = ("institution", "user", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = (
        "institution__display_name",
        "institution__legal_name",
        "user__email",
    )
    readonly_fields = ("id", "created_at", "updated_at")
