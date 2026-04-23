"""Configuration package for Django and background worker bootstrapping."""

from .celery_app import app as celery_app

__all__ = ("celery_app",)
