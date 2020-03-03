from flask import flash
import requests
import json
import xmltodict
# from app.blueprints.api.domain.godaddy import (
#     purchase_domain,
#     check_domain,
#     get_purchase_agreement,
#     get_tld_schema,
#     list_domains
# )
# from app.blueprints.api.domain.namecheap import purchase_domain
from app.blueprints.api.domain.domain import get_domain_details, get_dropping_domains
from app.blueprints.api.domain.dynadot import (
    check_domain,
    register_domain,
    get_domain_expiration,
    backorder_request,
    delete_backorder_request,
    get_domain_details,
    list_backorder_requests,
    list_contacts,
    set_whois_info,
    get_whois
)


def test(domain):
    # print(get_domain_details(domain))
    # get_purchase_agreement(domain)
    # get_tld_schema(domain)
    # list_domains(False)
    # check_domain(domain)

    # purchase = purchase_domain(domain)

    # purchase = purchase_domain(domain)

    # if purchase is None:
    #     flash("An error occurred while trying to purchase " + domain + ". Please try again.", 'error')
    # elif not purchase:
    #     flash(domain + " isn't available for purchase.", 'error')
    # elif purchase is True:
    #     flash("Successfully purchased " + domain + '.', 'success')
    # else:
    #     flash("There was an error", 'error')
    #     flash("The following error occurred: " + purchase['message'], 'error')

    # results = check_domain(domain)
    # results = backorder_request(domain)
    # results = register_domain(domain)
    # results = get_domain_details('rickycharpentier.xyz')
    # results = list_backorder_requests()
    # results = list_contacts()
    # results = set_whois_info('rickycharpentier.xyz')
    # results = get_whois(domain)
    results = get_dropping_domains()
    print(len(results))
    return results
