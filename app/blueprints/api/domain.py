from app.blueprints.api.namecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback
from flask import current_app
from instance.settings import NAMECHEAP_REGISTRATION


def register_domain(domain):
    try:
        username = current_app.config.get('NAMECHEAP_USERNAME')
        api_key = current_app.config.get('NAMECHEAP_API_KEY')
        ip_address = current_app.config.get('NAMECHEAP_IP_ADDRESS')

        api = Api(username, api_key, username, ip_address, sandbox=False)

        api.domains_create(DomainName=domain,
                           FirstName=NAMECHEAP_REGISTRATION['FirstName'],
                           LastName=NAMECHEAP_REGISTRATION['LastName'],
                           Address1=NAMECHEAP_REGISTRATION['Address1'],
                           City=NAMECHEAP_REGISTRATION['City'],
                           StateProvince=NAMECHEAP_REGISTRATION['StateProvince'],
                           PostalCode=NAMECHEAP_REGISTRATION['PostalCode'],
                           Country=NAMECHEAP_REGISTRATION['Country'],
                           Phone=NAMECHEAP_REGISTRATION['Phone'],
                           EmailAddress=NAMECHEAP_REGISTRATION['EmailAddress'],
                           )
        return True
    except Exception as e:
        print_traceback(e)
        return False


def check_domain(domain):
    try:
        username = current_app.config.get('NAMECHEAP_USERNAME')
        api_key = current_app.config.get('NAMECHEAP_API_KEY')
        ip_address = current_app.config.get('NAMECHEAP_IP_ADDRESS')

        api = Api(username, api_key, username, ip_address, sandbox=False)

        api.domains_check(domain)

        return True
    except Exception as e:
        print_traceback(e)
        return False
