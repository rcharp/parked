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
from dynadotpy.client import Dynadot


# Godaddy check domain availability
def check_domain(domain, test=True):
    try:
        # Get the GoDaddy keys
        api_key = current_app.config.get('GODADDY_TEST_API_KEY') if test else current_app.config.get('GODADDY_API_KEY')
        api_secret = current_app.config.get('GODADDY_TEST_SECRET_KEY') if test else current_app.config.get('GODADDY_SECRET_KEY')

        # Get the URL
        url = current_app.config.get('GODADDY_TEST_API_URL') if test else current_app.config.get('GODADDY_API_URL')
        url = url + '/v1/domains/available?domain=' + domain

        headers = {
            "Authorization": "sso-key " + api_key + ":" + api_secret,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        r = requests.get(url, headers=headers)

        # print(r.text)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            return None
    except Exception as e:
        print_traceback(e)
        return None


# Get WhoIs domain availability
def get_domain_availability(domain):
    details = dict()
    try:
        # Check GoDaddy first
        if check_domain(domain, False) is not None:
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


# GoDaddy purchase domain
def purchase_domain(domain, test=True):
    try:
        # Make sure the domain is available before trying to buy it
        availability = check_domain(domain, test)

        # Don't buy any domains that are more than $59
        if availability is not None and availability['available'] and availability['price'] <= 59990000:
            # Get the GoDaddy keys
            api_key = current_app.config.get('GODADDY_TEST_API_KEY') if test else current_app.config.get('GODADDY_API_KEY')
            api_secret = current_app.config.get('GODADDY_TEST_SECRET_KEY') if test else current_app.config.get('GODADDY_SECRET_KEY')

            # Get the URL
            url = current_app.config.get('GODADDY_TEST_API_URL') if test else current_app.config.get('GODADDY_API_URL')
            url = url + '/v1/domains/purchase'

            headers = {
                "Authorization": "sso-key " + api_key + ":" + api_secret,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            registration = current_app.config.get('NAMECHEAP_REGISTRATION')
            contact_info = {
                'addressMailing': {
                    'address1': registration['Address1'],
                    'address2': '',
                    'city': registration['City'],
                    'state': registration['StateProvince'],
                    'postalCode': registration['PostalCode'],
                    'country': 'US',
                },
                'email': registration['EmailAddress'],
                'fax': '',
                'jobTitle': 'owner',
                'nameFirst': registration['FirstName'],
                'nameLast': registration['LastName'],
                'nameMiddle': '',
                'organization': 'namecatcher.io',
                'phone': registration['Phone'],
            }

            body = json.dumps({
                'consent': {
                    'agreedAt': get_string_from_utc_datetime(datetime.datetime.now(pytz.utc), True),
                    'agreedBy': str(current_app.config.get('IP_ADDRESS')),
                    'agreementKeys': ['DNRA']
                },
                'contactAdmin': contact_info,
                'contactBilling': contact_info,
                'contactRegistrant': contact_info,
                'contactTech': contact_info,
                'domain': domain,
                'period': 1,
                'privacy': False,
                'renewAuto': True
            })

            r = requests.post(url, headers=headers, data=body)

            print(r.status_code)
            print(r.text)

            # Domain was successfully purchased
            if r.status_code == 200:
                return True
            else:
                return json.loads(r.text)
        elif availability is not None and not availability['available']:
            return False
        else:
            return None
    except Exception as e:
        print_traceback(e)
        return None


# Godaddy check domain
def list_domains(test=True):
    try:
        # Get the GoDaddy keys
        api_key = current_app.config.get('GODADDY_TEST_API_KEY') if test else current_app.config.get('GODADDY_API_KEY')
        api_secret = current_app.config.get('GODADDY_TEST_SECRET_KEY') if test else current_app.config.get('GODADDY_SECRET_KEY')

        # Get the URL
        url = current_app.config.get('GODADDY_TEST_API_URL') if test else current_app.config.get('GODADDY_API_URL')
        url = url + '/v1/domains'

        headers = {
            "Authorization": "sso-key " + api_key + ":" + api_secret,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        r = requests.get(url, headers=headers)

        print(r.text)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print_traceback(e)

        return None


# Godaddy Get Purchase Agreement
def get_purchase_agreement(domain, test=True):
    try:
        # Get the GoDaddy keys
        api_key = current_app.config.get('GODADDY_TEST_API_KEY') if test else current_app.config.get('GODADDY_API_KEY')
        api_secret = current_app.config.get('GODADDY_TEST_SECRET_KEY') if test else current_app.config.get('GODADDY_SECRET_KEY')

        # Get a list of TLDs for the purchase agreement
        ext = tldextract.extract(domain)
        tld = '.' + ext.suffix

        # Get the URL
        url = current_app.config.get('GODADDY_TEST_API_URL') if test else current_app.config.get('GODADDY_API_URL')
        url = url + '/v1/domains/agreements?tlds=' + tld + "&privacy=false"

        headers = {
            "Authorization": "sso-key " + api_key + ":" + api_secret,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        r = requests.get(url, headers=headers)

        print(r.status_code)
        print(r.text)

        if r.status_code == 200:
            return r
    except Exception as e:
        print_traceback(e)

        return None


# Godaddy get TLD Schema
def get_tld_schema(domain, test=True):
    try:
        # Get the GoDaddy keys
        api_key = current_app.config.get('GODADDY_TEST_API_KEY') if test else current_app.config.get('GODADDY_API_KEY')
        api_secret = current_app.config.get('GODADDY_TEST_SECRET_KEY') if test else current_app.config.get('GODADDY_SECRET_KEY')

        # Get a list of TLDs for the purchase agreement
        ext = tldextract.extract(domain)
        tld = ext.suffix

        # Get the URL
        url = current_app.config.get('GODADDY_TEST_API_URL') if test else current_app.config.get('GODADDY_API_URL')
        url = url + '/v1/domains/purchase/schema/' + tld

        headers = {
            "Authorization": "sso-key " + api_key + ":" + api_secret,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        r = requests.get(url, headers=headers)

        # print(r.status_code)
        # print(r.text)
        parsed = json.loads(r.text)
        print(json.dumps(parsed, indent=4, sort_keys=True))

        if r.status_code == 200:
            return json.loads(r.text)['properties']
    except Exception as e:
        print_traceback(e)

        return None