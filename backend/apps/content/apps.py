from django.apps import AppConfig


class ContentConfig(AppConfig):
    """Configuration for institution-authored content."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.content"
    verbose_name = "Content"
