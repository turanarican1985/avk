from django.apps import AppConfig


class InstitutionsConfig(AppConfig):
    """Configuration for the shared institution domain."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.institutions"
    verbose_name = "Institutions"
