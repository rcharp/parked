from flask import Blueprint, render_template, json, flash
from flask import redirect, url_for, current_app
from importlib import import_module
from app.blueprints.api.api_functions import print_traceback
from app.extensions import csrf
from flask import request
from app.blueprints.api.domain.domain import (
    purchase_domain,
    check_domain,
    get_domain_details,
    get_purchase_agreement,
    get_tld_schema,
    list_domains
)

api = Blueprint('api', __name__, template_folder='templates')


@api.route('/connect/<app>')
def connect(app):
    try:
        module = import_module("app.blueprints.api.apps." + app + '.' + app)
        auth_link = module.auth()

        return redirect(auth_link)
    except Exception as e:
        print_traceback(e)
        flash("There was an error connecting to this app. Please try again.", 'error')
        return redirect(url_for('user.dashboard'))


@api.route('/test', methods=['GET','POST'])
@csrf.exempt
def test():
    if request.method == 'POST':
        domain = request.form['domain']

        try:
            # print(get_domain_details(domain))
            # get_purchase_agreement(domain)
            # get_tld_schema(domain)
            # list_domains(False)
            # check_domain(domain)

            purchase = purchase_domain(domain)

            if purchase is None:
                print("An error occurred.")
                # Redirect to dashboard with an error
            elif not purchase:
                print("This domain is not available for purchase.")
                # Redirect to the dashboard with an error
            else:
                print("Successfully purchased domain.")
            return redirect(url_for('user.dashboard'))
        except Exception as e:
            print_traceback(e)
            flash("There was an error buying this domain. Please try again.", 'error')
            return redirect(url_for('user.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))
