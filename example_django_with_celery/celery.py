import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_django_with_celery.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Development")

import configurations

configurations.setup()

app = Celery("example_django_with_celery")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)