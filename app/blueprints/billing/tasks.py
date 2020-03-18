from app.app import create_celery_app
from datetime import datetime, date, timezone, timedelta
from sqlalchemy import or_, and_, cast, Date as d
from app.blueprints.user.models import User
from app.blueprints.api.models.backorder import Backorder
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
def delete_domains(user_ids):
    """
    Delete users and potentially cancel their subscription.

    :param user_ids: List of ids to be deleted
    :type user_ids: list
    :return: int
    """
    from app.blueprints.api.models.backorder import Backorder
    from app.blueprints.api.models.domains import Domain
    from app.blueprints.api.models.searched import SearchedDomain
    from app.blueprints.billing.models.customer import Customer

    for id in user_ids:
        # Delete backorders and domains
        b = Backorder.query.filter(Backorder.user_id == id).all()
        d = Domain.query.filter(Domain.user_id == id).all()
        s = SearchedDomain.query.filter(SearchedDomain.user_id == id).all()
        c = Customer.query.filter(Customer.user_id == id).all()

        for backorder in b:
            if backorder is None:
                continue
            backorder.delete()

        for domain in d:
            if domain is None:
                continue
            domain.delete()

        for searched in s:
            if searched is None:
                continue
            searched.delete()

        for customer in c:
            if customer is None:
                continue
            customer.delete()


@celery.task()
def delete_backorders(ids):
    """
    Delete users and potentially cancel their subscription.

    :param ids: List of ids to be deleted
    :type ids: list
    :return: int
    """
    return Backorder.bulk_delete(ids)


@celery.task()
def cancel():
    return c
