from app.blueprints.api.domain.pynamecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback, active_backorders
from app.blueprints.page.date import (
    get_string_from_utc_datetime,
    convert_timestamp_to_datetime_utc,
    get_dt_string,
    get_utc_date,
    get_utc_date_today_string
)
from flask import current_app, flash
from app.extensions import db
import pythonwhois
import datetime
import tldextract
import pytz
import time
from sqlalchemy import exists, and_
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

    # print(results)

    if 'Available' in results:
        if 'Price' in results:
            price = format(Decimal(re.findall("\d*\.?\d+", results['Price'])[0]) + 49, '.2f')
        else:
            price = None
        available = True if results['Available'] == 'yes' else False

        # Testing purposes. Set Price to $1
        # price = format(1.00, '.2f')

        details.update({'name': domain, 'available': available, 'price': price})
        return details
    else:
        return None
    # dyn = Dynadot(api_key=current_app.config.get('DYNADOT_API_KEY'))
    # return dyn.search(domains=[domain])


def register_domain(domain, backordered=False):
    try:
        # Get the production level
        production = True#current_app.config.get('PRODUCTION')

        # Price limit for purchasing a domain
        limit = 60 if backordered else 99

        # Only send a request if it isn't already processing one
        if is_processing():
            register_domain(domain, backordered)

        # Ensure that the domain can be registered
        price = Decimal(get_domain_price(domain))

        if price is None or price > limit:
            return {'domain': domain, 'success': False}

        # The real deal. The domain will be registered if the app is being used live
        # Otherwise return True in the dev environment
        if not production:
            return "Domain " + domain + " bought in test for " + str(price) + "."

        api_key = current_app.config.get('DYNADOT_API_KEY')
        dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=register&duration=1&domain=' + domain + '&duration=1'
        r = requests.get(url=dynadot_url)
        results = json.loads(json.dumps(xmltodict.parse(r.text)))['RegisterResponse']['RegisterHeader']
        print(results)

        if 'SuccessCode' in results and results['SuccessCode'] == '0':
            return {'domain': domain, 'success': True}
        return {'domain': domain, 'success': False}
    except Exception as e:
        print_traceback(e)
        return {'success': False}


def order_domains():
    from app.blueprints.api.models.backorder import Backorder

    # Create a list of results
    results = list()

    # Get the backorders that are dropping today
    today = get_utc_date_today_string()
    backorders = Backorder.query.filter(and_(Backorder.date_available == today, Backorder.secured.is_(False))).all()

    # Try to register the backorders
    # If successful, change the 'success' attribute on the backorder in the db
    for backorder in backorders:
        result = register_domain(backorder.domain_name, True)
        if result['success']:
            backorder.secured = True
            backorder.save()

        results.append(result)

    # Return the successful backorders
    return results


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
    # Only send a request if it isn't already processing one
    if is_processing():
        get_domain_price(domain)

    api_key = current_app.config.get('DYNADOT_API_KEY')
    dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=search&domain0=' + domain + "&show_price=1"

    r = requests.get(url=dynadot_url)
    results = json.loads(json.dumps(xmltodict.parse(r.text)))['Results']['SearchResponse']['SearchHeader']

    price = None
    if 'Available' in results:
        if 'Price' in results:
            price = format(Decimal(re.findall("\d*\.?\d+", results['Price'])[0]) + 49, '.2f')

    return price


def backorder_request(domain):
    # Only send a request if it isn't already processing one
    if is_processing():
        backorder_request(domain)
    try:
        # "Pending Delete" is in the domain's status, so it can be backordered now
        pending_delete = is_pending_delete(domain)
        if pending_delete:
            api_key = current_app.config.get('DYNADOT_API_KEY')
            dynadot_url = "https://api.dynadot.com/api3.xml?key=" + api_key + '&command=add_backorder_request&domain=' + domain
            r = requests.get(url=dynadot_url)

            results = json.loads(json.dumps(xmltodict.parse(r.text)))
            response = results['AddBackorderRequestResponse']['AddBackorderRequestHeader']
            # print(response)

            return response['SuccessCode'] == '0' or 'Error' in response and 'is already on your backorder request list' in response['Error']

        # Still create the backorder in the db, but set backorder.pending_delete to False
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
# This needs to be here because importing it from domain.Domainr creates a circular dependency
# Returns true if "pending delete" is in the domain's status, meaning it can be attempted to be purchased
def is_pending_delete(domain):
    try:

        # If the domain is in the Drops table, then it's pending delete
        from app.blueprints.api.models.drops import Drop
        if db.session.query(exists().where(Drop.name == domain)).scalar():
            return True

        api_key = current_app.config.get('X_RAPID_API_KEY')
        url = "https://domainr.p.rapidapi.com/v2/status"
        querystring = {"domain": domain}

        headers = {
            'x-rapidapi-host': "domainr.p.rapidapi.com",
            'x-rapidapi-key': api_key
        }

        r = requests.get(url=url, headers=headers, params=querystring)
        results = json.loads(r.text)['status']

        if len(results) > 0 and 'status' in results[0] and results[0]['status'] == 'deleting':
            return True
        return False
    except Exception as e:
        print_traceback(e)
    return False

    # Old PythonWhois code
    # try:
    #     ext = tldextract.extract(domain)
    #     domain = ext.registered_domain
    #
    #     details = pythonwhois.get_whois(domain)
    #
    #     # Remove the raw data
    #     status = details['status']
    #     return any('pendingDelete' in x for x in status)
    # except Exception as e:
    #     print_traceback(e)
    #     return False


def get_whois(domain):
    # details = pythonwhois.get_whois(domain)
    # del details['raw']
    import pywhois as p
    details = p.whois(domain)
    return details

