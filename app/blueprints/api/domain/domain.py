from app.blueprints.api.domain.namecheap.namecheap import Api
from app.blueprints.api.api_functions import print_traceback
from flask import current_app


def purchase_domain(domain, sandbox=True):
    try:
        username = current_app.config.get('NAMECHEAP_USERNAME')
        ip_address = current_app.config.get('HOME_IP_ADDRESS')
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
