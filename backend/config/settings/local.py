"""Local development settings for AVK."""

from .base import *  # noqa: F403,F401
from .base import BASE_DIR, env_bool

DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if env_bool("USE_SQLITE", default=True):
    DATABASES = {  # type: ignore[assignment]
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
