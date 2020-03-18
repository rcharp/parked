import time
from operator import itemgetter
from itertools import groupby
from heapq import merge
from flask import current_app
import sqlalchemy as sa

from lib.flask_mailplus import send_template_message
from app.extensions import cache, db
from app.app import create_celery_app
from app.blueprints.user.models import User


celery = create_celery_app()

send = True


@celery.task()
def deliver_password_reset_email(user_id, reset_token):
    """
    Send a reset password e-mail to a user.

    :param user_id: The user id
    :type user_id: int
    :param reset_token: The reset token
    :type reset_token: str
    :return: None if a user was not found
    """
    user = User.query.get(user_id)

    if user is None:
        return

    ctx = {'user': user, 'reset_token': reset_token}

    send_template_message(subject='Password reset from Domain',
                          recipients=[user.email],
                          template='user/mail/password_reset', ctx=ctx)

    return None


# Sending emails -------------------------------------------------------------------
@celery.task()
def send_welcome_email(email):
    from app.blueprints.user.emails import send_welcome_email

    if send:
        send_welcome_email(email)
    return


@celery.task()
def send_reservation_email(email, domain, available):
    from app.blueprints.user.emails import send_reservation_email
    if send:
        send_reservation_email(email, domain, available)
    return


@celery.task()
def send_secured_email(email, domain):
    from app.blueprints.user.emails import send_secured_email
    if send:
        send_secured_email(email, domain)
    return


@celery.task()
def send_purchase_email(email, domain):
    from app.blueprints.user.emails import send_purchase_email
    if send:
        send_purchase_email(email, domain)
    return


@celery.task()
def send_contact_us_email(email, message):
    from app.blueprints.user.emails import contact_us_email
    if send:
        contact_us_email(email, message)
    return


@celery.task()
def send_cancel_email(email):
    from app.blueprints.user.emails import send_cancel_email
    if send:
        send_cancel_email(email)
    return


