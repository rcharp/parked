from flask import flash
from app.blueprints.api.domain.domain import (
    purchase_domain,
    check_domain,
    get_domain_details,
    get_purchase_agreement,
    get_tld_schema,
    list_domains,
    namecheap_purchase_domain
)


def test(domain):
    # print(get_domain_details(domain))
    # get_purchase_agreement(domain)
    # get_tld_schema(domain)
    # list_domains(False)
    # check_domain(domain)

    purchase = purchase_domain(domain)

    # purchase = namecheap_purchase_domain(domain)

    if purchase is None:
        flash("An error occurred while trying to purchase " + domain + ". Please try again.", 'error')
    elif not purchase:
        flash(domain + " isn't available for purchase.", 'error')
    elif purchase is True:
        flash("Successfully purchased " + domain + '.', 'success')
    else:
        flash("There was an error", 'error')
        # flash("The following error occurred: " + purchase['message'], 'error')
