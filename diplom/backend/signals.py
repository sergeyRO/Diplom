from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created

from backend.models import ConfirmEmailToken, User

# from netology_pd_diplom.celery import send_email_token, \
#     send_email_reg, send_email_order, send_email_order_adm, \
#     send_email_order_contact
from netology_pd_diplom.celery import app

# from backend.views import yaml_in_db
#
#
# @app.task
# def do_import(file, request):
#     return yaml_in_db(file, request)

# @app.task
# def send_email_token(sender, instance, reset_password_token, **kwargs):
#     #return password_reset_token_created(sender, instance, reset_password_token, **kwargs)
#     return password_reset_token_created(sender, reset_password_token)
# @app.task
# def send_email_reg(user_id, **kwargs):
#     return new_user_registered_signal(user_id, **kwargs)
# @app.task
# def send_email_order(user_id, **kwargs):
#     return new_order_signal(user_id, **kwargs)
# @app.task
# def send_email_order_adm(user_id, **kwargs):
#     return new_order_admin_signal(user_id, **kwargs)
# @app.task
# def send_email_order_contact(user_id, **kwargs):
#     return new_order_contact_signal(user_id, **kwargs)

new_user_registered = Signal('user_id')

new_order = Signal('user_id')

new_order_admin = Signal()

new_order_contact = Signal('user_id')

@app.task
def send_message(user_id, **kwargs):
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)
    subject, from_email, to = f"Password Reset Token for {token.user.email}", settings.EMAIL_HOST_USER, token.user.email
    text_content = token.key
    #html_content = '<p>This is an <strong>important</strong> message.</p>'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    #msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Отправляем письмо с токеном для сброса пароля
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param kwargs:
    :return:
    """
    # send an e-mail to the user

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {reset_password_token.user}",
        # message:
        reset_password_token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [reset_password_token.user.email]
    )
    msg.send()


@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
    # send an e-mail to the user
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {token.user.email}",
        # message:
        token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [token.user.email]
    )
    msg.send()


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    """
    отправяем письмо при изменении статуса заказа
    """
    # send an e-mail to the user
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Обновление статуса заказа",
        # message:
        'Заказ сформирован',
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()


@receiver(new_order_admin)
def new_order_admin_signal(user_id, **kwargs):
    """
    отправяем письмо админу после создания заказа
    """
    # send an e-mail to the user

    msg = EmailMultiAlternatives(
        # title:
        f"Обновление статуса заказа",
        # message:
        'Заказ сформирован',
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        settings.EMAIL_ADMIN
    )
    msg.send()


@receiver(new_order_contact)
def new_order_contact_signal(user_id, **kwargs):
    """
    отправяем письмо при изменении статуса заказа
    """

    # send an e-mail to the user
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Обновление статуса заказа",
        # message:
        'Заказ сформирован\n'
        'Проверьте корректность адреса доставки ниже\n'
        f'{kwargs["comment"]}',
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()
