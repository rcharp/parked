from flask import Blueprint, render_template, flash
from app.extensions import cache, timeout
from config import settings
from app.extensions import db, csrf
from flask import redirect, url_for, request, current_app
from flask_login import current_user, login_required
import requests
import ast
import json
import traceback
from sqlalchemy import and_, exists, text
from importlib import import_module
import os
import random

page = Blueprint('page', __name__, template_folder='templates')


@page.route('/')
def home():
    test = not current_app.config.get('PRODUCTION')
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    from app.blueprints.api.domain.domain import get_dropping_domains, get_drop_count
    from app.blueprints.api.api_functions import active_tlds

    dropping, drop_count = get_dropping_domains(40)

    return render_template('page/index.html',
                           plans=settings.STRIPE_PLANS,
                           dropping=dropping,
                           test=test,
                           drop_count=drop_count,
                           tlds=active_tlds())


@page.route('/<domain>/', methods=['GET'])
@csrf.exempt
def parked(domain):
    if domain is not None:
        from app.blueprints.api.models.domains import Domain
        if db.session.query(exists().where(and_(Domain.name == domain, Domain.registered.is_(True)))).scalar():
            return render_template('page/domain.html', domain=domain)

    return redirect(url_for('page.home'))


@page.route('/availability', methods=['GET','POST'])
@csrf.exempt
def availability():
    if request.method == 'POST':

        from app.blueprints.api.api_functions import save_search
        from app.blueprints.api.domain.domain import get_domain_availability, get_domain_details, get_dropping_domains, get_domain

        domain_name = get_domain(request.form['domain'])
        if domain_name is None:
            flash("This domain is invalid. Please try again.", "error")
            return redirect(url_for('page.home'))

        domain = get_domain_availability(domain_name)

        # 500 is the error returned if the domain is valid but can't be backordered
        if domain == 500:
            flash("This domain extension can't be backordered. Please try another domain extension.", "error")
            return redirect(url_for('page.home'))

        if domain is not None and 'available' in domain and domain['available'] is not None:
            # Save the search if it is a valid domain
            if domain['available'] is not None:
                save_search(domain_name, domain['expires'], domain['date_available'], 3)  # '3' is the admin ID

            details = get_domain_details(domain_name)
            dropping = get_dropping_domains()

            return render_template('page/index.html', domain=domain, details=details, dropping=dropping)

        flash("This domain is invalid. Please try again.", "error")
        return redirect(url_for('page.home'))

    return render_template('page/index.html', plans=settings.STRIPE_PLANS)


@page.route('/view/<domain>/<available>', methods=['GET','POST'])
@csrf.exempt
def view(domain, available):

    if current_user.is_authenticated:
        id = current_user.id
    else:
        id = 0

    available = available.replace('-', '/')
    from app.blueprints.api.api_functions import save_search
    save_search(domain, available, available, id)
    return render_template('page/view.html', domain=domain, available=available)


# @page.route('/drops/<tld>', methods=['GET','POST'])
@page.route('/drops', methods=['GET','POST'])
@csrf.exempt
def drops():
    from app.blueprints.api.api_functions import active_tlds
    from app.blueprints.api.domain.domain import get_dropping_domains
    from app.blueprints.api.domain.s3 import get_last_modified

    domains, drop_count = get_dropping_domains()
    last_updated = get_last_modified()

    return render_template('user/drops.html',
                           listing=None,
                           domains=domains,
                           tlds=active_tlds(),
                           drop_count=drop_count,
                           current_user=current_user,
                           last_updated=last_updated)


@page.route('/terms')
def terms():
    return render_template('page/terms.html')


@page.route('/privacy')
def privacy():
    return render_template('page/privacy.html')


@page.route('/index')
def index():
    return render_template('page/index.html', plans=settings.STRIPE_PLANS)


# Callbacks.
@page.route('/callback/<app>', methods=['GET', 'POST'])
@csrf.exempt
def callback(app):
    module = import_module("app.blueprints.api.apps." + app + "." + app)
    app_callback = getattr(module, 'callback')
    return app_callback(request)


# Webhooks -------------------------------------------------------------------
@page.route('/webhook/<app>', methods=['GET','POST'])
@csrf.exempt
def webhook(app):
    try:
        module = import_module("app.blueprints.api.apps." + app + ".webhook")
        call_webhook = getattr(module, 'webhook')

        return call_webhook(request)
    except Exception:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


# Pagination for /drops route
class PageResult:
    def __init__(self, data, tld, page = 1, number = 20):
        self.__dict__ = dict(zip(['data', 'tld', 'page', 'number'], [data, tld, page, number]))
        self.full_listing = [self.data[i:i+number] for i in range(0, len(self.data), number)]
    def __iter__(self):
        for i in self.full_listing[self.page-1]:
            yield i
    def __repr__(self): #used for page linking
        # return "/drops/{0}/{1}".format(self.tld, str(self.page+1)) #view the next page
        return '/drops/' + str(self.tld) + '/' + str(int(self.page)+1)