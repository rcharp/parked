from app.blueprints.api.domain.pynamecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback, valid_tlds, pool_tlds, park_tlds, tld_length, active_tlds
from app.blueprints.page.date import get_string_from_utc_datetime, get_utc_date_today_string, get_dt_string, convert_datetime_to_available
from flask import current_app, flash
import pythonwhois
import datetime
import tldextract
from flask import abort, request
from math import ceil
import pytz
import requests
import json
import random
from app.extensions import db
from sqlalchemy import exists, func, and_
from app.blueprints.api.domain.dynadot import check_domain
from os import path
import os
# import numpy as np


def get_domain(domain):
    try:
        from app.blueprints.api.api_functions import format_domain_search
        domain = format_domain_search(domain)
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

            # If this is a dropping domain, update the available date. Not using this anymore since no longer using Drops table
            # from app.blueprints.api.models.drops import Drop
            # if db.session.query(exists().where(Drop.name == domain)).scalar():
            #     drop = Drop.query.filter(Drop.name == domain).scalar()
            #     availability.update({'date_available': drop.date_available})

            if 'expiration_date' in details and len(details['expiration_date']) > 0 and details['expiration_date'][0] is not None:
                expires = get_dt_string(details['expiration_date'][0])
                availability.update({'expires': expires})

                # Old way to calculate date_available. Returns in format Month Day, Year (e.g. January 1, 2020)
                # date_available = get_dt_string(details['expiration_date'][0] + datetime.timedelta(days=78))

                if 'date_available' not in availability:
                    availability.update({'date_available': convert_datetime_to_available(details['expiration_date'][0] + datetime.timedelta(days=78))})
            else:
                if 'date_available' not in availability:
                    availability.update({'date_available': None})

                availability.update({'expires': None})
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


def get_registered_date(domain):
    try:
        ext = tldextract.extract(domain)
        domain = ext.registered_domain
        details = pythonwhois.get_whois(domain)

        if 'creation_date' in details:
            return details['creation_date'][0]
        return None
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


def get_dropping_domains(limit=None):

    if limit is not None:
        if not path.exists("selection.json") or os.path.exists("selection.json") and os.stat("selection.json").st_size == 0:
            return create_selection(limit)
        else:
            selection = list()
            num_domains = '{:,}'.format(count_lines(open("domains.json")))
            with open("selection.json", "r") as file:
                lines = file.readlines()
                for line in lines:
                    selection.append(json.loads(line))

                random.shuffle(selection)
                return selection, num_domains

    # If the file exists, pull the drops from there
    if path.exists("domains.json"):
        with open('domains.json', 'r') as file:
            domains = list()
            lines = file.readlines()

            for line in lines:
                domains.append(json.loads(line))
            domains.sort(key=lambda x: x['name'])
            return domains, '{:,}'.format(len(domains))

    # If there is no file, then generate all drops
    else:
        from app.blueprints.api.domain.s3 import get_content
        domains = get_content(limit)
        return domains, '{:,}'.format(get_drop_count())


def create_selection(limit):
    num_domains = '{:,}'.format(count_lines(open("domains.json")))
    today = get_utc_date_today_string()
    domains = list()
    counter = 0

    if not path.exists("domains.json"):
        from app.blueprints.api.domain.s3 import get_content
        return get_content(limit), num_domains

    with open("domains.json", "r") as file:
        words = open('app/blueprints/api/domain/words/words.txt').read().splitlines()
        lines = file.readlines()

        selection = [x for x in lines if json.loads(x)['date_available'] != today]
        selection = random.sample(selection, k=int(len(selection) / 2))
        for line in selection:
            line = json.loads(line)

            if has_word(words, line):
                domains.append(line)
                counter += 1

            if counter == limit: break

        # Delete the selection file if it exists
        if path.exists("selection.json"):
            os.remove("selection.json")

        with open('selection.json', 'a') as output:
            for domain in domains:
                json.dump(domain, output)
                output.write(os.linesep)

        # Shuffle the limited selection
        random.shuffle(domains)
        return domains, num_domains


def generate_drops():
    try:
        # The max number of domains to get, per TLD
        limit = 1500

        from app.blueprints.api.domain.download import pool_domains, park_domains

        if path.exists("domains.json"):
            os.remove("domains.json")

        # Get the domains from the Pool list and the Park list
        pool = pool_domains(limit)
        park = park_domains(limit)

        if pool or park:
            with open('domains.json', 'r') as output:

                # Upload to AWS
                from app.blueprints.api.domain.s3 import upload_to_aws
                return upload_to_aws(output.name, 'namecatcherio', output.name)
    except Exception as e:
        print_traceback(e)
        return False


def get_drop_count():
    from app.blueprints.api.domain.s3 import get_content
    return get_content(get_count=True)


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


def delete_backorders():
    try:
        from app.blueprints.api.models.backorder import Backorder
        backorders = Backorder.query.filter(and_(Backorder.paid.is_(True), Backorder.secured.is_(True))).all()

        for backorder in backorders:
            backorder.delete()

    except Exception as e:
        print_traceback(e)


def lost_backorders(domain):
    try:
        from app.blueprints.api.models.backorder import Backorder
        backorders = Backorder.query.filter(and_(Backorder.domain_name == domain, Backorder.secured.is_(False))).all()

        for backorder in backorders:
            backorder.lost = True
            backorder.save()

    except Exception as e:
        print_traceback(e)


def write_drops_to_db(drops, limit):
    from app.blueprints.api.models.drops import Drop

    for drop in drops:
        if db.session.query(Drop).count() > limit:
            return

        if not db.session.query(exists().where(Drop.name == drop['name'])).scalar():
            d = Drop()
            d.name = drop['name']
            d.date_available = drop['date_available']
            d.save()


def count_lines(file):
    for i, l in enumerate(file):
        pass
    return i + 1


def has_word(words, line):
    domain = line['name'].split('.')[0]
    if any(x in domain and (len(domain) <= 10) and (5 <= len(x) <= 7) and '-' not in domain for x in words):
        return True
    return False
