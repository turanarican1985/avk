from django.apps import AppConfig


class StaffOpsConfig(AppConfig):
    """Configuration for staff roles, permissions, and operational policy."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.staff_ops"
    verbose_name = "Staff Operations"
