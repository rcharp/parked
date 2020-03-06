from app.blueprints.api.domain.pynamecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback, valid_tlds, pool_tlds, park_tlds, tld_length
from app.blueprints.page.date import get_string_from_utc_datetime
from flask import current_app, flash
from app.blueprints.page.date import get_dt_string
import pythonwhois
import datetime
import tldextract
import pytz
import requests
import json
import random
from app.extensions import db
from sqlalchemy import exists, func, and_
from app.blueprints.api.domain.dynadot import check_domain


def get_domain(domain):
    try:
        ext = tldextract.extract(domain)
        domain = ext.registered_domain
        return domain
    except Exception as e:
        return None


# Get WhoIs domain availability
def get_domain_availability(domain):

    # Get the availability
    availability = check_domain(domain)

    try:
        if availability is not None:

            # If the TLD is invalid and the domain can't be purchased outright, show an error.
            tld = get_domain_tld(domain)
            if (tld is None or tld not in valid_tlds()) and not availability['available']:
                return 500

            ext = tldextract.extract(domain)
            domain = ext.registered_domain

            details = pythonwhois.get_whois(domain)
            if 'expiration_date' in details and len(details['expiration_date']) > 0 and details['expiration_date'][0] is not None:
                expires = get_dt_string(details['expiration_date'][0])
                available_on = get_dt_string(details['expiration_date'][0] + datetime.timedelta(days=78))
                availability.update({'expires': expires, 'available_on': available_on})
            else:
                availability.update({'expires': None, 'available_on': None})
    except Exception as e:
        print_traceback(e)

    return availability


# WhoIs get domain registration details
def get_domain_details(domain):
    try:
        ext = tldextract.extract(domain)
        domain = ext.registered_domain
        details = pythonwhois.get_whois(domain)

        # Remove the raw data
        del details['raw']

        return details
    except Exception as e:
        print_traceback(e)
        return None


# Get WhoIs domain availability
def get_domain_expiration(domain):
    try:
        ext = tldextract.extract(domain)
        domain = ext.registered_domain
        details = pythonwhois.get_whois(domain)
        if 'expiration_date' in details and len(details['expiration_date']) > 0 and details['expiration_date'][0] is not None:
            expires = get_dt_string(details['expiration_date'][0])
            return expires
        return None
    except Exception as e:
        print_traceback(e)
        return None


# WhoIs get domain registration details
def get_domain_tld(domain):
    try:
        ext = tldextract.extract(domain)
        tld = ext.suffix
        if tld is not None:
            return '.' + tld

        return None
    except Exception as e:
        print_traceback(e)
        return None


# WhoIs get status of domain
def get_domain_status(domain):
    try:
        ext = tldextract.extract(domain)
        domain = ext.registered_domain
        details = pythonwhois.get_whois(domain)

        # Remove the raw data
        del details['raw']

        return True
    except Exception as e:
        print_traceback(e)
        return False


def get_dropping_domains():
    domains = list()
    from app.blueprints.api.models.drops import Drop
    drops = Drop.query.order_by(func.random()).limit(40).all()
    for drop in drops:
        domains.append({'name': drop.name, 'date_available': drop.date_available})

    return domains


def delete_dropping_domains():
    from app.blueprints.api.models.drops import Drop
    Drop.query.delete()
    if db.session.query(Drop).count() == 0:
        return True
    return False


def set_dropping_domains(drops, limit):
    from app.blueprints.api.models.drops import Drop

    for drop in drops:
        if db.session.query(Drop).count() > limit:
            return

        if not db.session.query(exists().where(Drop.name == drop['name'])).scalar():
            d = Drop()
            d.name = drop['name']
            d.date_available = drop['date_available']
            d.save()


def generate_drops():
    try:
        # The max number of domains to get, per TLD
        limit = 500

        # Do not generate more drops if there are too many in the db
        from app.blueprints.api.models.drops import Drop
        if db.session.query(Drop).count() > limit * tld_length():
            return False

        from app.blueprints.api.domain.download import pool_domains, park_domains

        # Get the domains from the Pool list and the Park list
        pool = pool_domains(limit)  # .delay()
        park = park_domains(limit)  # .delay()

        domains = pool + park

        # We got at least one domain
        if len(domains) > 0:
            if delete_dropping_domains():
                set_dropping_domains(domains, limit * tld_length())
                return True

        return False
    except Exception as e:
        print_traceback(e)
        return False


def retry_charges():
    try:
        from app.blueprints.api.models.backorder import Backorder
        from app.blueprints.api.models.domains import Domain
        from app.blueprints.billing.charge import charge_card
        backorders = Backorder.query.filter(and_(Backorder.paid.is_(False), Backorder.secured.is_(True))).all()

        for backorder in backorders:
            domain = Domain.query.filter(Domain.id == backorder.domain).scalar()

            # The domain doesn't exist or it hasn't been registered, so don't charge the card.
            if domain is None or not domain.registered:
                continue

            # Charge the customer's card. Leave uncommented until live.
            if charge_card(backorder.pi, backorder.pm) is not None:
                backorder.paid = True
                backorder.save()

    except Exception as e:
        print_traceback(e)
