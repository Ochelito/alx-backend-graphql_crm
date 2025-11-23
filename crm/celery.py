from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")

# Initialize Celery app
app = Celery("crm")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
