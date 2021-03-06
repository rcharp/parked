from flask import flash
import requests
import json
import xmltodict
from app.blueprints.api.domain.domain import get_domain_details, get_dropping_domains#, generate_drops
from app.blueprints.api.domain.domainr import get_domain_status
from app.blueprints.api.domain.dynadot import (
    register_domain,
    get_domain_expiration,
    backorder_request,
    delete_backorder_request,
    # get_domain_details,
    list_backorder_requests,
    list_contacts,
    set_whois_info,
    get_whois,
    order_domains,
    forward_domain
)
from app.blueprints.api.domain.s3 import download_from_aws

from celery.result import AsyncResult


def test(domain):
    from app.blueprints.api.domain.domain import generate_drops
    from app.blueprints.api.domain.download import pool_domains, park_domains

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

    # results = is_pending_delete('digitalcard.io')
    # results = backorder_request('digitalcard.io')
    # results = register_domain('rickycharpentier3.io')
    # results = get_domain_details('upload.io')
    # results = list_backorder_requests()
    # results = list_contacts()
    # results = set_whois_info('rickycharpentier.xyz')
    # results = get_whois(domain)
    # results = get_dropping_domains()
    # results = is_pending_delete('digitalcard.io')

    # results = generate_drops()
    # results = park_domains(500)

    # TODO: This WILL order the domains. Be very careful.
    # results = order_domains()

    # results = generate_drops()

    # results = forward_domain('photocamp.io')
    results = download_from_aws('domains.json')
    return results


# def run_test(test_number):
#     results = tests[test_number]
#     return results
