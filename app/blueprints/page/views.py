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


@page.route('/availability', methods=['GET','POST'])
@csrf.exempt
def availability():
    if request.method == 'POST':

        from app.blueprints.api.api_functions import save_search
        from app.blueprints.api.domain.domain import get_domain_availability, get_domain_details, get_dropping_domains, get_domain
        from app.blueprints.api.models.drops import Drop

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
        id = 3

    available = available.replace('-', '/')
    from app.blueprints.api.api_functions import save_search
    save_search(domain, available, available, id)
    return render_template('page/view.html', domain=domain, available=available)


@page.route('/drops', methods=['GET','POST'])
@csrf.exempt
def drops():
    from app.blueprints.api.api_functions import active_tlds
    from app.blueprints.api.domain.domain import get_drop_count, get_dropping_domains
    from app.blueprints.api.domain.filestack import get_content

    domains, drop_count = get_dropping_domains()

    return render_template('user/drops.html', domains=domains, tlds=active_tlds(), drop_count=drop_count, current_user=current_user)


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
