from app.blueprints.api.domain.pynamecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback
from app.blueprints.page.date import get_string_from_utc_datetime, convert_timestamp_to_datetime_utc
from flask import current_app, flash
from app.blueprints.page.date import get_dt_string
import pythonwhois
import datetime
import tldextract
import pytz
import requests
import json
import re
from decimal import Decimal
from dynadotpy.client import Dynadot
import xmltodict


def check_domain(domain):
    api_key = current_app.config.get('DYNADOT_API_KEY')
    dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=search&domain0=' + domain + "&show_price=1"

    details = dict()

    r = requests.get(url=dynadot_url)
    results = json.loads(json.dumps(xmltodict.parse(r.text)))['Results']['SearchResponse']['SearchHeader']

    if 'Available' in results:
        price = re.findall("\d*\.?\d+", results['Price'])[0] if 'Price' in results else None
        available = True if results['Available'] == 'yes' else False
        details.update({'name': domain, 'available': available, 'price': price})
        return details
    else:
        return None
    # dyn = Dynadot(api_key=current_app.config.get('DYNADOT_API_KEY'))
    # return dyn.search(domains=[domain])


def register_domain(domain, production=False):

    # Ensure that the domain can be registered
    results = check_domain(domain)
    print(results)

    # The real deal. The domain will be registered if 'production' is passed as True
    if production:
        # Only purchase the domain if it's less than $60
        if results is not None and results['price'] is not None and Decimal(results['price']) <= 60:
            api_key = current_app.config.get('DYNADOT_API_KEY')
            dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=register&duration=1&domain=' + domain
            r = requests.get(url=dynadot_url)
            results = json.loads(json.dumps(xmltodict.parse(r.text)))['RegisterResponse']['RegisterHeader']
            return results
    return False


def get_domain_expiration(domain):
    # Ensure that the domain can be registered
    api_key = current_app.config.get('DYNADOT_API_KEY')
    dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=domain_info&domain=' + domain
    r = requests.get(url=dynadot_url)

    results = json.loads(json.dumps(xmltodict.parse(r.text)))['DomainInfoResponse']['DomainInfoContent']['Domain']['Expiration']

    expires = convert_timestamp_to_datetime_utc(float(results)/1000)
    expires = get_dt_string(expires)
    return expires


def get_domain_details(domain):
    # Ensure that the domain can be registered
    api_key = current_app.config.get('DYNADOT_API_KEY')
    dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=domain_info&domain=' + domain
    r = requests.get(url=dynadot_url)

    results = json.loads(json.dumps(xmltodict.parse(r.text)))['DomainInfoResponse']['DomainInfoContent']['Domain']

    return results