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
from app.blueprints.page.date import is_date
from app.blueprints.api.pynamecheap import namecheap as nc


# Create a distinct integration id for the integration.
def generate_id(size=8, chars=string.digits):

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
    return


# Create a distinct auth id for the auth.
def generate_auth_id(size=6, chars=string.digits):
    return
    # Generate a random 8-character user id
    auth_id = int(''.join(random.choice(chars) for _ in range(size)))

    from app.blueprints.api.models.app_auths import AppAuthorization

    # Check to make sure there isn't already that id in the database
    if not db.session.query(exists().where(AppAuthorization.id == auth_id)).scalar():
        return auth_id
    else:
        generate_auth_id()


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


def check_domain_availability(domains):
    username = current_app.config.get('NAMECHEAP_USERNAME')
    api_key = current_app.config.get('NAMECHEAP_API_KEY')
    ip_address = current_app.config.get('NAMECHEAP_IP_ADDRESS')

    api = nc.Api(username, api_key, username, ip_address, sandbox=False)

    availability = []

    for domain in domains:
        try:
            available = api.domains_check(domain)
            availability.append({domain: available})
        except Exception as e:
            print_traceback(e)
            continue

    return availability
