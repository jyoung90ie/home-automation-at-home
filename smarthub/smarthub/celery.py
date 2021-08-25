"""Module for defining celery tasks"""
import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarthub.settings")

app = Celery("smarthub")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Default recommended implementation to tag request to worker job"""
    print(f"Request: {self.request!r}")
