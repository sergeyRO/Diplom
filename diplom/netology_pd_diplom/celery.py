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


@app.task
def send_email_token(sender, instance, reset_password_token, **kwargs):
    return password_reset_token_created(sender, instance, reset_password_token, **kwargs)
@app.task
def send_email_reg(user_id, **kwargs):
    return new_user_registered_signal(user_id, **kwargs)
@app.task
def send_email_order(user_id, **kwargs):
    return new_order_signal(user_id, **kwargs)
@app.task
def send_email_order_adm(user_id, **kwargs):
    return new_order_admin_signal(user_id, **kwargs)
@app.task
def send_email_order_contact(user_id, **kwargs):
    return new_order_contact_signal(user_id, **kwargs)

@app.task
def do_import(file, request):
    return yaml_in_db(file, request)