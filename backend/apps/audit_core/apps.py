from django.apps import AppConfig


class AuditCoreConfig(AppConfig):
    """Configuration for shared audit and traceability primitives."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit_core"
    verbose_name = "Audit Core"
