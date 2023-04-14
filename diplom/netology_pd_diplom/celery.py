import os

from celery import Celery
from backend.views import yaml_in_db
from backend.signals import password_reset_token_created,\
    new_user_registered_signal, new_order_signal,\
    new_order_admin_signal, new_order_contact_signal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "netology_pd_diplom.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()