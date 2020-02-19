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


# Namecheap check domain
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


# Namecheap purchase domain
def purchase_domain(domain, sandbox=True):
    try:
        username = current_app.config.get('NAMECHEAP_USERNAME')
        ip_address = current_app.config.get('IP_ADDRESS')
        api_key = current_app.config.get('NAMECHEAP_SANDBOX_API_KEY') if sandbox else current_app.config.get('NAMECHEAP_API_KEY')

        api = Api(username, api_key, username, ip_address, sandbox=sandbox)
        registration = current_app.config.get('NAMECHEAP_REGISTRATION')

        api.domains_create(DomainName=domain,
                           FirstName=registration['FirstName'],
                           LastName=registration['LastName'],
                           Address1=registration['Address1'],
                           City=registration['City'],
                           StateProvince=registration['StateProvince'],
                           PostalCode=registration['PostalCode'],
                           Country=registration['Country'],
                           Phone=registration['Phone'],
                           EmailAddress=registration['EmailAddress'],
                           )
        return True
    except Exception as e:
        print_traceback(e)
        return False