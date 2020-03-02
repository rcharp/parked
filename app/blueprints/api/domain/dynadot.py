from app.blueprints.api.domain.pynamecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback, active_backorders
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
from builtins import any


def check_domain(domain):
    # Only send a request if it isn't already processing one
    if is_processing():
        check_domain(domain)
    api_key = current_app.config.get('DYNADOT_API_KEY')
    dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=search&domain0=' + domain + "&show_price=1"

    details = dict()

    r = requests.get(url=dynadot_url)
    results = json.loads(json.dumps(xmltodict.parse(r.text)))['Results']['SearchResponse']['SearchHeader']

    print(results)

    if 'Available' in results:
        if 'Price' in results:
            price = format(Decimal(re.findall("\d*\.?\d+", results['Price'])[0]) + 49, '.2f')
        else:
            price = None
        available = True if results['Available'] == 'yes' else False

        # Testing purposes. Set Price to $1
        price = format(1.00, '.2f')

        details.update({'name': domain, 'available': available, 'price': price})
        return details
    else:
        return None
    # dyn = Dynadot(api_key=current_app.config.get('DYNADOT_API_KEY'))
    # return dyn.search(domains=[domain])


def register_domain(domain, backordered=False):

    # Get the production level
    production = current_app.config.get('PRODUCTION')

    # Only send a request if it isn't already processing one
    if is_processing():
        register_domain(domain)
    # Ensure that the domain can be registered
    results = check_domain(domain)

    limit = 60 if backordered else 99

    # The real deal. The domain will be registered if the app is being used live
    if production:
        # Only purchase the domain if it's less than $60
        if results is not None and 'price' in results and results['price'] is not None and Decimal(results['price']) <= limit:
            api_key = current_app.config.get('DYNADOT_API_KEY')
            dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=register&duration=1&domain=' + domain
            r = requests.get(url=dynadot_url)
            results = json.loads(json.dumps(xmltodict.parse(r.text)))['RegisterResponse']['RegisterHeader']
            return 'SuccessCode' in results and results['SuccessCode'] == '0'

    # Otherwise return True in the dev environment
    return True


def get_domain_expiration(domain):
    # Only send a request if it isn't already processing one
    if is_processing():
        get_domain_expiration(domain)
    # Ensure that the domain can be registered
    api_key = current_app.config.get('DYNADOT_API_KEY')
    dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=domain_info&domain=' + domain
    r = requests.get(url=dynadot_url)

    if r.status_code == 200:
        results = json.loads(json.dumps(xmltodict.parse(r.text)))
        if 'DomainInfoResponse' in results and 'DomainInfoContent' in results['DomainInfoResponse'] and 'Domain' in results['DomainInfoResponse']['DomainInfoContent'] and 'Expiration' in results['DomainInfoResponse']['DomainInfoContent']['Domain']:
            results = json.loads(json.dumps(xmltodict.parse(r.text)))['DomainInfoResponse']['DomainInfoContent']['Domain']['Expiration']

            expires = convert_timestamp_to_datetime_utc(float(results)/1000)
            expires = get_dt_string(expires)

            return expires
    return None


def get_domain_details(domain):
    # Only send a request if it isn't already processing one
    if is_processing():
        get_domain_details(domain)
    # Ensure that the domain can be registered
    api_key = current_app.config.get('DYNADOT_API_KEY')
    dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=domain_info&domain=' + domain
    r = requests.get(url=dynadot_url)

    results = json.loads(json.dumps(xmltodict.parse(r.text)))#  ['DomainInfoResponse']['DomainInfoContent']['Domain']

    return results


def get_domain_contact_info(domain):
    # Only send a request if it isn't already processing one
    if is_processing():
        get_domain_contact_info(domain)
    # Ensure that the domain can be registered
    api_key = current_app.config.get('DYNADOT_API_KEY')
    dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=domain_info&domain=' + domain
    r = requests.get(url=dynadot_url)

    results = json.loads(json.dumps(xmltodict.parse(r.text)))['DomainInfoResponse']['DomainInfoContent']['Domain']['Whois']

    return results


def get_domain_price(domain):
    # Get the domain's details, which include the price
    details = check_domain(domain)

    if 'price' in details:
        return details['price'] + 4900
    else:
        return None


def backorder_request(domain):
    # Only send a request if it isn't already processing one
    if is_processing():
        backorder_request(domain)
    try:
        # "Pending Delete" is in the domain's status, so it can be backordered now
        if get_domain_status(domain):
            api_key = current_app.config.get('DYNADOT_API_KEY')
            dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=add_backorder_request&domain=' + domain
            r = requests.get(url=dynadot_url)

            results = json.loads(json.dumps(xmltodict.parse(r.text)))
            response = results['AddBackorderRequestResponse']['AddBackorderRequestHeader']

            return response['SuccessCode'] == '0' or 'Error' in response and 'is already on your backorder request list' in response['Error']

        # Still create the backorder in the db, but set backorder.available to False
        return False
    except Exception as e:
        print_traceback(e)

    return False


def delete_backorder_request(domain):
    # Only send a request if it isn't already processing one
    if is_processing():
        delete_backorder_request(domain)
    if not active_backorders(domain):
        try:
            api_key = current_app.config.get('DYNADOT_API_KEY')
            dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=delete_backorder_request&domain=' + domain
            r = requests.get(url=dynadot_url)
            return True
        except Exception as e:
            print_traceback(e)
            return False
    return False


def set_whois_info(domain):
    if is_processing():
        set_whois_info(domain)
    try:
        contact = '602028'
        api_key = current_app.config.get('DYNADOT_API_KEY')
        dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=set_whois&domain=' + domain + "&registrant_contact=" + contact + "&admin_contact=" + contact + "&technical_contact=" + contact + "&billing_contact=" + contact
        r = requests.get(url=dynadot_url)

        results = json.loads(json.dumps(xmltodict.parse(r.text)))

        return results['SetWhoisResponse']['SetWhoisHeader']['SuccessCode'] == '0'
    except Exception as e:
        print_traceback(e)
        return None


def list_contacts():
    if is_processing():
        list_contacts()
    try:
        api_key = current_app.config.get('DYNADOT_API_KEY')
        dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=contact_list'
        r = requests.get(url=dynadot_url)

        results = json.loads(json.dumps(xmltodict.parse(r.text)))
        return results
    except Exception as e:
        print_traceback(e)
        return None


def list_backorder_requests():
    if is_processing():
        list_backorder_requests()
    try:
        api_key = current_app.config.get('DYNADOT_API_KEY')
        dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=backorder_request_list'
        r = requests.get(url=dynadot_url)

        results = json.loads(json.dumps(xmltodict.parse(r.text)))

        return results
    except Exception as e:
        print_traceback(e)
        return None


def is_processing():
    api_key = current_app.config.get('DYNADOT_API_KEY')
    dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=is_processing'
    r = requests.get(url=dynadot_url)

    results = json.loads(json.dumps(xmltodict.parse(r.text)))
    response = results['Response']['ResponseHeader']['ResponseMsg']

    return response == 'yes'


# Helper methods -------------------------------------------------------------------------------
# This needs to be here because importing it from domain.domain creates a circular dependency
# Returns true if "pending delete" is in the domain's status, meaning it can be backordered
def get_domain_status(domain):
    # Only send a request if it isn't already processing one
    if is_processing():
        get_domain_status(domain)
    try:
        ext = tldextract.extract(domain)
        domain = ext.registered_domain

        details = pythonwhois.get_whois(domain)

        # Remove the raw data
        status = details['status']
        return any('pendingDelete' in x for x in status)
    except Exception as e:
        print_traceback(e)
        return False


def get_whois(domain):
    # details = pythonwhois.get_whois(domain)
    # del details['raw']
    import pywhois as p
    details = p.whois(domain)
    return details

