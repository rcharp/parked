from app.app import create_celery_app
from datetime import datetime, date, timezone, timedelta
from sqlalchemy import or_, and_, cast, Date as d
from app.blueprints.user.models import User
from app.blueprints.billing.models.credit_card import CreditCard
from app.blueprints.billing.views.billing import cancel as c
from app.blueprints.page.date import get_datetime_from_string, convert_timestamp_to_datetime_utc

celery = create_celery_app()


@celery.task()
def mark_old_credit_cards():
    """
    Mark credit cards that are going to expire soon or have expired.

    :return: Result of updating the records
    """
    return CreditCard.mark_old_credit_cards()


@celery.task()
def delete_users(ids):
    """
    Delete users and potentially cancel their subscription.

    :param ids: List of ids to be deleted
    :type ids: list
    :return: int
    """
    return User.bulk_delete(ids)


@celery.task()
def cancel():
    return c
