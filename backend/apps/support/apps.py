from django.apps import AppConfig


class SupportConfig(AppConfig):
    """Configuration for support intake and case handling concerns."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.support"
    verbose_name = "Support"
