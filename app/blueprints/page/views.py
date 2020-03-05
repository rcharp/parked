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
from sqlalchemy import and_, exists
from importlib import import_module
import os
import random

page = Blueprint('page', __name__, template_folder='templates')


@page.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    from app.blueprints.api.domain.domain import get_dropping_domains
    dropping = get_dropping_domains()

    test = not current_app.config.get('PRODUCTION')

    # Shuffle the domains to spice things up a little
    # random.shuffle(dropping)
    return render_template('page/index.html', plans=settings.STRIPE_PLANS, dropping=dropping, test=test)


@page.route('/availability', methods=['GET','POST'])
@csrf.exempt
def availability():
    if request.method == 'POST':

        from app.blueprints.api.api_functions import valid_tlds
        from app.blueprints.api.domain.domain import get_domain_availability, get_domain_details, get_dropping_domains
        from app.blueprints.api.models.drops import Drop

        domain_name = request.form['domain'].replace(' ', '').lower()
        domain = get_domain_availability(domain_name)

        # 500 is the error returned if the domain is valid but can't be backordered
        if domain == 500:
            flash("This domain extension can't be backordered. Please try another domain extension.", "error")
            return redirect(url_for('page.home'))

        if domain is not None and 'available' in domain and domain['available'] is not None:

            # Save the search if it is a valid domain
            # if domain['available'] is not None:
            #     save_search(domain_name, domain['expires'], current_user.id)

            details = get_domain_details(domain_name)
            dropping = get_dropping_domains()

            # There is a Drop in the db for this domain, so update the available date
            if db.session.query(exists().where(Drop.name == domain['name'])).scalar():
                drop = Drop.query.filter(Drop.name == domain['name']).scalar()
                if drop is not None:
                    domain.update({'available_on': drop.date_available})

            return render_template('page/index.html', domain=domain, details=details, dropping=dropping)

        flash("This domain is invalid. Please try again.", "error")
        return redirect(url_for('page.home'))

    return render_template('page/index.html', plans=settings.STRIPE_PLANS)


@page.route('/view', methods=['GET','POST'])
@csrf.exempt
def view():
    if request.method == 'POST':
        domain = ast.literal_eval(request.form['domain'])
        return render_template('page/view.html', domain=domain)

    return redirect(url_for('page.home'))


@page.route('/drops', methods=['GET','POST'])
@csrf.exempt
def drops():
    from app.blueprints.api.models.drops import Drop
    from app.blueprints.api.api_functions import dropping_tlds
    domains = Drop.query.all()
    return render_template('user/drops.html', domains=domains, tlds=dropping_tlds())


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