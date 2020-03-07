import re
import sys
import time
import pytz
import string
import random
import requests
import traceback
from datetime import datetime
from collections import defaultdict
from app.extensions import db
from sqlalchemy import exists, and_, or_, inspect
from flask import current_app
from importlib import import_module
from app.blueprints.page.date import get_dt_string


# Create a distinct integration id for the integration.
def generate_id(size=12, chars=string.digits):
    # Generate a random 12-character user id
    new_id = int(''.join(random.choice(chars) for _ in range(size)))

    from app.blueprints.api.models.domains import Domain

    # Check to make sure there isn't already that id in the database
    if not db.session.query(exists().where(Domain.order_id == new_id)).scalar():
        return new_id
    else:
        generate_id()


# Create a distinct auth id for the auth.
def generate_auth_id(size=6, chars=string.digits):
    return
    # Generate a random 8-character user id
    # auth_id = int(''.join(random.choice(chars) for _ in range(size)))
    #
    # from app.blueprints.api.models.app_auths import AppAuthorization
    #
    # # Check to make sure there isn't already that id in the database
    # if not db.session.query(exists().where(AppAuthorization.id == auth_id)).scalar():
    #     return auth_id
    # else:
    #     generate_auth_id()


# Create a distinct integration id for the integration.
def generate_app_id(size=6, chars=string.digits):
    return
    # # Generate a random 8-character user id
    # app_id = int(''.join(random.choice(chars) for _ in range(size)))
    #
    # from app.blueprints.api.models.apps import App
    #
    # # Check to make sure there isn't already that id in the database
    # if not db.session.query(exists().where(App.id == app_id)).scalar():
    #     return app_id
    # else:
    #     generate_app_id()


def print_traceback(e):
    traceback.print_tb(e.__traceback__)
    print(e)


def save_domain(user_id, customer_id, domain, expires, date_available, reserve_time, registered=False):
    from app.blueprints.api.models.domains import Domain

    d = Domain()
    d.user_id = user_id
    d.name = domain
    d.expires = expires
    d.date_available = date_available
    d.created_on = get_dt_string(reserve_time)
    d.customer_id = customer_id
    d.registered = registered

    d.save()
    return d


def save_search(domain, expires, date_available, user_id):
    from app.blueprints.api.models.searched import SearchedDomain

    if not db.session.query(exists().where(and_(SearchedDomain.name == domain, SearchedDomain.user_id == user_id))).scalar():
        s = SearchedDomain()
        s.name = domain
        s.expires = expires
        s.date_available = date_available
        s.user_id = user_id

        s.save()
    return


def format_domain_search(domain):
    if domain is not None:
        domain = domain.replace(' ', '').lower()
        domain = domain.replace('https://www.', '').replace('https://', '').replace('http://', '').replace('www.','')
        return domain
    return None


def create_backorder(domain, pm, pi, customer_id, user_id, pending_delete):
    from app.blueprints.api.models.backorder import Backorder

    b = Backorder()
    b.domain = domain.id
    b.pm = pm
    b.pi = pi
    b.domain_name = domain.name
    b.expires = domain.expires
    b.date_available = domain.date_available
    b.user_id = user_id
    b.customer_id = customer_id
    b.active = True
    b.pending_delete = pending_delete
    b.secured = False
    b.paid = False

    b.save()
    return


def active_backorders(domain):
    from app.blueprints.api.models.backorder import Backorder
    if not db.session.query(exists().where(and_(Backorder.domain_name == domain, Backorder.active.is_(True)))).scalar():
        return False
    return True


def update_customer(pm, customer_id, save_card):
    from app.blueprints.billing.charge import update_customer
    return update_customer(pm, customer_id, save_card)


def valid_tlds():
    return ['.com', '.net', '.org', '.co', '.io', '.pro', '.ly', '.cc', '.us', '.biz', '.info', '.mobi', '.bio', '.me', '.tv', '.pro', '.red', '.blue', '.black', '.pink', '.green', '.kim', '.poker', '.organic', '.lgbt', '.bet', '.vote', '.voto', '.promo', '.archi', '.ski']


def pool_tlds():
    return ['.io', '.com', '.info', '.us', '.org', '.net']


def park_tlds():
    return ['.me', '.pro']


def active_tlds():
    return pool_tlds() + park_tlds()


def tld_length():
    return len(pool_tlds()) + len(park_tlds())