from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Configuration for shared cross-cutting backend utilities."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
    verbose_name = "Common"
