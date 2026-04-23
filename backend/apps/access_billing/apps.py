from django.apps import AppConfig


class AccessBillingConfig(AppConfig):
    """Configuration for commercial access and billing concerns."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.access_billing"
    verbose_name = "Access Billing"
