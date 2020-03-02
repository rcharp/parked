from app.blueprints.api.domain.pynamecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback, valid_tlds
from app.blueprints.page.date import get_string_from_utc_datetime
from flask import current_app, flash
from app.blueprints.page.date import get_dt_string
import pythonwhois
import datetime
import tldextract
import pytz
import requests
import json
from app.blueprints.api.domain.dynadot import check_domain


# Get WhoIs domain availability
def get_domain_availability(domain):

    # Get the availability
    availability = check_domain(domain)

    try:
        if availability is not None:

            # If the TLD is invalid and the domain can't be purchased outright, show an error.
            tld = get_domain_tld(domain)
            if (tld is None or tld not in valid_tlds()) and not availability['available']:
                return None

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


