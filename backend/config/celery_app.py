"""Celery application bootstrap for asynchronous work."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("avk")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
