from django.apps import AppConfig


class InstitutionVerificationConfig(AppConfig):
    """Configuration for institution verification concerns."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.institution_verification"
    verbose_name = "Institution Verification"
