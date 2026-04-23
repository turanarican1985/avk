from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """Configuration for verified review concerns."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reviews"
    verbose_name = "Reviews"
