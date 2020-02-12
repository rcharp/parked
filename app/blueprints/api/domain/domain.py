from app.blueprints.api.domain.namecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback
from flask import current_app
import pythonwhois
import tldextract
import pytz
import requests
import json
from requests.auth import HTTPBasicAuth


# Namecheap purchase
# def purchase_domain(domain, sandbox=True):
#     try:
#         username = current_app.config.get('NAMECHEAP_USERNAME')
#         ip_address = current_app.config.get('HOME_IP_ADDRESS')
#         api_key = current_app.config.get('NAMECHEAP_SANDBOX_API_KEY') if sandbox else current_app.config.get('NAMECHEAP_API_KEY')
#
#         api = Api(username, api_key, username, ip_address, sandbox=sandbox)
#         registration = current_app.config.get('NAMECHEAP_REGISTRATION')
#
#         api.domains_create(DomainName=domain,
#                            FirstName=registration['FirstName'],
#                            LastName=registration['LastName'],
#                            Address1=registration['Address1'],
#                            City=registration['City'],
#                            StateProvince=registration['StateProvince'],
#                            PostalCode=registration['PostalCode'],
#                            Country=registration['Country'],
#                            Phone=registration['Phone'],
#                            EmailAddress=registration['EmailAddress'],
#                            )
#         return True
#     except Exception as e:
#         print_traceback(e)
#         return False


# GoDaddy purchase
def purchase_domain(domain, test=True):
    try:
        # Get the GoDaddy keys
        api_key = current_app.config.get('GODADDY_TEST_API_KEY') if test else current_app.config.get('GODADDY_API_KEY')
        api_secret = current_app.config.get('GODADDY_TEST_SECRET_KEY') if test else current_app.config.get('GODADDY_SECRET_KEY')

        # Get the URL
        url = current_app.config.get('GODADDY_TEST_API_URL') if test else current_app.config.get('GODADDY_API_URL')
        url = url + '/v1/domains/purchase'

        headers = {
            "Authorization": "sso-key " + api_key + ":" + api_secret,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # agreed_at = datetime.datetime.now(pytz.utc)
        # agreed_by = current_app.config.get('IP_ADDRESS')

        r = requests.post(url, headers=headers, data=get_tld_schema(domain))

        print(r.status_code)
        print(r.text)

        if r.status_code == 200:
            return r
    except Exception as e:
        print_traceback(e)
        return


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

        if r.status_code == 200:
            return json.dumps(r.text)
    except Exception as e:
        print_traceback(e)

        return None


def get_domain_details(domain):
    try:
        ext = tldextract.extract(domain)
        domain = ext.registered_domain

        details = pythonwhois.get_whois(domain)

        # Remove the raw data
        del details['raw']

        # Format the entries

        return details
    except Exception as e:
        print_traceback(e)
        return None


def check_domain(domain, sandbox=True):
    try:
        username = current_app.config.get('NAMECHEAP_USERNAME')
        ip_address = current_app.config.get('HOME_IP_ADDRESS')
        api_key = current_app.config.get('NAMECHEAP_SANDBOX_API_KEY') if sandbox else current_app.config.get('NAMECHEAP_API_KEY')

        api = Api(username, api_key, username, ip_address, sandbox=sandbox)

        api.domains_check(domain)

        return True
    except Exception as e:
        print_traceback(e)
        return False
