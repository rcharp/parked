from flask import flash
# from app.blueprints.api.domain.godaddy import (
#     purchase_domain,
#     check_domain,
#     get_purchase_agreement,
#     get_tld_schema,
#     list_domains
# )
# from app.blueprints.api.domain.namecheap import purchase_domain
from app.blueprints.api.domain.domain import get_domain_details
from app.blueprints.api.domain.dynadot import (
    check_domain,
    register_domain
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

    results = check_domain(domain)
    # results = register_domain(domain)
    return results
