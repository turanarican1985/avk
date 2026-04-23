from django.apps import AppConfig


class ContentModerationConfig(AppConfig):
    """Configuration for content moderation concerns."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.content_moderation"
    verbose_name = "Content Moderation"
