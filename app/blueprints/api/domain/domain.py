from app.blueprints.api.domain.pynamecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback
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
    details = dict()
    try:
        # Check dynadot first
        if check_domain(domain) is not None:
            ext = tldextract.extract(domain)
            domain = ext.registered_domain

            details = pythonwhois.get_whois(domain)
            if 'expiration_date' in details and len(details['expiration_date']) > 0 and details['expiration_date'][0] is not None:
                expires = get_dt_string(details['expiration_date'][0])
                details.update({'name': domain, 'available': False, 'expires': expires})
            else:
                details.update({'name': domain, 'available': True, 'expires': None})
        else:
            details.update({'name': domain, 'available': None, 'expires': None})
    except Exception as e:
        print_traceback(e)
        details.update({'name': domain, 'available': None, 'expires': None})

    return details


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
