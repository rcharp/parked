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
# from app.blueprints.api.pynamecheap import namecheap as nc
# from app.blueprints.api.namecheapapi.namecheapapi.api.domains import DomainAPI
# import app.blueprints.api.domain.pythonwhois
import pythonwhois
import tldextract


# Create a distinct integration id for the integration.
def generate_id(size=8, chars=string.digits):
    return
    # # Generate a random 8-character user id
    # new_id = int(''.join(random.choice(chars) for _ in range(size)))
    #
    # from app.blueprints.api.models.user_integrations import UserIntegration
    #
    # # Check to make sure there isn't already that id in the database
    # if not db.session.query(exists().where(UserIntegration.id == new_id)).scalar():
    #     return integration_id
    # else:
    #     generate_integration_id()


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


def check_domain_availability(domain):
    details = dict()
    try:
        ext = tldextract.extract(domain)
        domain = ext.registered_domain

        details = pythonwhois.get_whois(domain)
        if 'expiration_date' in details and len(details['expiration_date']) > 0 and details['expiration_date'][0] is not None:
            expires = get_dt_string(details['expiration_date'][0])
            details.update({'name': domain, 'available': False, 'expires': expires})
        else:
            details.update({'name': domain, 'available': True, 'expires': None})
    except Exception as e:
        print_traceback(e)
        details.update({'name': domain, 'available': None, 'expires': None})

    return details


def save_domain(user_id, customer_id, domain, expires, reserve_time):
    from app.blueprints.api.models.domains import Domain

    d = Domain()
    d.user_id = user_id
    d.name = domain
    d.expires = expires
    d.created_on = get_dt_string(reserve_time)
    d.customer_id = customer_id

    d.save()
    return


def update_customer(pm, customer_id):
    from app.blueprints.billing.charge import update_customer
    return update_customer(pm, customer_id)
