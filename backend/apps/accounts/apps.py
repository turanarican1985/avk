from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the custom user and account boundary."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"
