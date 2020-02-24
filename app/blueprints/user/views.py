from flask import (
    Blueprint,
    redirect,
    request,
    flash,
    Markup,
    url_for,
    render_template,
    json,
    jsonify,
    session)
from flask_login import (
    login_required,
    login_user,
    current_user,
    logout_user)

import time

from lib.safe_next_url import safe_next_url
from app.blueprints.user.decorators import anonymous_required
from app.blueprints.user.models import User
from app.blueprints.user.forms import (
    LoginForm,
    BeginPasswordResetForm,
    PasswordResetForm,
    SignupForm,
    WelcomeForm,
    UpdateCredentials)

import re
import os
import pytz
import stripe
import datetime
from datetime import datetime as dt
from app.extensions import cache, csrf, timeout, db
from importlib import import_module
from sqlalchemy import or_, and_, exists
from app.blueprints.billing.charge import (
    stripe_checkout,
    create_payment,
    delete_payment,
    confirm_intent,
    get_payment_method,
    get_card
)
from app.blueprints.api.models.domains import Domain
from app.blueprints.billing.models.customer import Customer
from app.blueprints.api.models.searched import SearchedDomain
from app.blueprints.api.api_functions import (
    save_domain,
    save_search,
    valid_tlds,
    update_customer,
    print_traceback,
    create_backorder
)
from app.blueprints.api.domain.domain import get_domain_details, get_domain_availability, get_domain_tld
from app.blueprints.api.domain.dynadot import (
    register_domain as register,
    delete_backorder_request,
    get_domain_expiration,
    backorder_request
)

user = Blueprint('user', __name__, template_folder='templates')


# Login and Credentials -------------------------------------------------------------------
@user.route('/login', methods=['GET', 'POST'])
@anonymous_required()
# @cache.cached(timeout=timeout)
@csrf.exempt
def login():
    form = LoginForm(next=url_for('user.dashboard'))

    if form.validate_on_submit():

        u = User.find_by_identity(request.form.get('identity'))

        if u and u.authenticated(password=request.form.get('password')):
            # As you can see remember me is always enabled, this was a design
            # decision I made because more often than not users want this
            # enabled. This allows for a less complicated login form.
            #
            # If however you want them to be able to select whether or not they
            # should remain logged in then perform the following 3 steps:
            # 1) Replace 'True' below with: request.form.get('remember', False)
            # 2) Uncomment the 'remember' field in user/forms.py#LoginForm
            # 3) Add a checkbox to the login form with the id/name 'remember'
            if login_user(u, remember=True) and u.is_active():
                u.update_activity_tracking(request.remote_addr)

                # Set the days left in the trial
                if current_user.trial:
                    trial_days_left = 14 - (datetime.datetime.now() - current_user.created_on.replace(tzinfo=None)).days
                    if trial_days_left < 0:
                        current_user.trial = False
                        current_user.save()

                next_url = request.form.get('next')

                if next_url:
                    return redirect(safe_next_url(next_url))

                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
            else:
                flash('This account has been disabled.', 'error')
        else:
            flash('Your username/email or password is incorrect.', 'error')

    else:
        print(form.errors)

    return render_template('user/login.html', form=form)


@user.route('/logout')
@login_required
# @cache.cached(timeout=timeout)
def logout():
    logout_user()

    flash('You have been logged out.', 'success')
    return redirect(url_for('user.login'))


@user.route('/account/begin_password_reset', methods=['GET', 'POST'])
@anonymous_required()
def begin_password_reset():
    form = BeginPasswordResetForm()

    if form.validate_on_submit():
        u = User.initialize_password_reset(request.form.get('identity'))

        flash('An email has been sent to {0}.'.format(u.email), 'success')
        return redirect(url_for('user.login'))

    return render_template('user/begin_password_reset.html', form=form)


@user.route('/account/password_reset', methods=['GET', 'POST'])
@anonymous_required()
def password_reset():
    form = PasswordResetForm(reset_token=request.args.get('reset_token'))

    if form.validate_on_submit():
        u = User.deserialize_token(request.form.get('reset_token'))

        if u is None:
            flash('Your reset token has expired or was tampered with.',
                  'error')
            return redirect(url_for('user.begin_password_reset'))

        form.populate_obj(u)
        u.password = User.encrypt_password(request.form.get('password'))
        u.save()

        if login_user(u):
            flash('Your password has been reset.', 'success')
            return redirect(url_for('user.dashboard'))

    return render_template('user/password_reset.html', form=form)


@user.route('/signup', methods=['GET', 'POST'])
@anonymous_required()
@csrf.exempt
# @cache.cached(timeout=timeout)
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        u = User()

        form.populate_obj(u)
        u.password = User.encrypt_password(request.form.get('password'))
        u.save()

        if login_user(u):

            from app.blueprints.user.tasks import send_welcome_email
            from app.blueprints.contact.mailerlite import create_subscriber

            send_welcome_email.delay(current_user.email)
            create_subscriber(current_user.email)

            flash("You've successfully signed up!", 'success')
                
            return redirect(url_for('user.dashboard'))

    return render_template('user/signup.html', form=form)


@user.route('/welcome', methods=['GET', 'POST'])
@login_required
def welcome():
    if current_user.username:
        flash('You already picked a username.', 'warning')
        return redirect(url_for('user.dashboard'))

    form = WelcomeForm()

    if form.validate_on_submit():
        current_user.username = request.form.get('username')
        current_user.save()

        flash('Your username has been set.', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/welcome.html', form=form, payment=current_user.payment_id)


@user.route('/settings/update_credentials', methods=['GET', 'POST'])
@login_required
def update_credentials():
    form = UpdateCredentials(current_user, uid=current_user.id)

    if form.validate_on_submit():
        new_password = request.form.get('password', '')
        current_user.email = request.form.get('email')

        if new_password:
            current_user.password = User.encrypt_password(new_password)

        current_user.save()

        flash('Your sign in settings have been updated.', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/update_credentials.html', form=form)


# Dashboard -------------------------------------------------------------------
@user.route('/dashboard', methods=['GET','POST'])
@login_required
@csrf.exempt
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))

    test = False

    domains = Domain.query.filter(Domain.user_id == current_user.id).all()
    searched = SearchedDomain.query.filter(SearchedDomain.user_id == current_user.id).limit(20).all()
    tlds = valid_tlds()

    return render_template('user/dashboard.html', current_user=current_user, domains=domains, test=test, searched=searched, tlds=tlds)


# Domain Functions -------------------------------------------------------------------
@user.route('/check_availability', methods=['GET','POST'])
@login_required
@csrf.exempt
def check_availability():
    if request.method == 'POST':
        # Uncomment this when ready to check multiple domains at once
        # domains = [l for l in request.form['domains'].split('\n') if l]
        
        domain_name = request.form['domain'].replace(' ','').lower()
        tld = get_domain_tld(domain_name)
        if tld not in valid_tlds():
            flash("This TLD can't be backordered. Please try another TLD.", "error")
            return redirect(url_for('user.dashboard'))

        domain = get_domain_availability(domain_name)
        details = get_domain_details(domain_name)

        # Save the search if it is a valid domain
        if domain is not None and domain['available'] is not None:
            save_search(domain_name, domain['expires'], current_user.id)

            domains = Domain.query.filter(Domain.user_id == current_user.id).all()
            return render_template('user/dashboard.html', current_user=current_user, domain=domain, details=details, domains=domains)
        flash("The domain was invalid. Please try again.", "error")
        return redirect(url_for('user.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))


@user.route('/register_domain', methods=['GET','POST'])
@login_required
@csrf.exempt
def register_domain():
    # Get and register the domain
    if request.method == 'POST':
        domain_id = request.form['domain']
        domain = Domain.query.filter(and_(Domain.user_id == current_user.id), Domain.id == domain_id).scalar()

        if register(domain.name) or True:
            domain.registered = True
            domain.save()

            flash('This domain has been registered.', 'success')
        else:
            flash('This domain has not been registered.', 'error')
    return redirect(url_for('user.dashboard'))


@user.route('/view_domain', methods=['GET','POST'])
@csrf.exempt
def view_domain():
    # Get the domain details and display them
    if request.method == 'POST':
        domain_id = request.form['domain']
        domain = Domain.query.filter(and_(Domain.user_id == current_user.id), Domain.id == domain_id).scalar()
        details = get_domain_details(domain.name)
        registered = domain.registered

        return render_template('user/view.html', current_user=current_user, domain=domain.name, details=details, registered=registered)

    else:
        try:
            domain_name = request.args.get('domain')
            domain = Domain.query.filter(and_(Domain.user_id == current_user.id), Domain.name == domain_name).scalar()
            details = get_domain_details(domain_name)
            registered = domain.registered

            return render_template('user/view.html', current_user=current_user, domain=domain.name, details=details, registered=registered)
        except Exception as e:
            flash("There was an error. Please try again.", 'error')
    return redirect(url_for('user.dashboard'))


@user.route('/delete_domain', methods=['GET','POST'])
@csrf.exempt
def delete_domain():

    # Get and delete the domain
    if request.method == 'POST':
        domain_id = request.form['domain']
        domain = Domain.query.filter(and_(Domain.user_id == current_user.id), Domain.id == domain_id).scalar()
        order_id = domain.pm

        domain.delete()
        delete_backorder_request(domain.name)

        # Ensure the domain has been deleted
        d = Domain.query.get(domain_id)
        if d is None:
            # Delete the Payment Intent
            # delete_payment(order_id)
            flash('This domain reservation was successfully deleted.', 'success')
        else:
            flash('There was a problem deleting your reservation. Please try again.', 'error')

    return redirect(url_for('user.dashboard'))


@user.route('/update_domain', methods=['GET','POST'])
@csrf.exempt
def update_domain():
    if request.method == 'POST':
        if 'domain' in request.form and 'customer_id' in request.form:
            domain = request.form['domain']
            customer_id = request.form['customer_id']

            # Send a receipt email

            # Now that the domain has been registered, get the expiry to update the db
            expires = get_domain_expiration(domain)

            # Create and save the domain in the db if it isn't already
            if not db.session.query(exists().where(and_(Domain.name == domain, Domain.user_id == current_user.id))).scalar():
                d = Domain()
                d.user_id = current_user.id
                d.customer_id = customer_id
                d.registered = True
                d.name = domain
                d.expires = expires

                d.save()
            else:
                d = Domain.query.filter(and_(Domain.name == domain, Domain.user_id == current_user.id)).scalar()
                d.customer_id = customer_id
                d.registered = True
                d.expires = expires
                d.save()

    return redirect(url_for('user.dashboard'))


# Reserve/Backorder Domain -------------------------------------------------------------------
@user.route('/reserve_domain', methods=['GET','POST'])
@login_required
@csrf.exempt
def reserve_domain():
    if request.method == 'POST':
        domain = request.form['domain']

        if db.session.query(exists().where(and_(Domain.name == domain, Domain.user_id == current_user.id))).scalar():

            # Deletes the domain if it already exists. For testing purposes. Remove this when done testing.
            # d = Domain.query.filter(and_(Domain.name == domain, Domain.user_id == current_user.id)).scalar()
            # d.delete()

            flash('You already have this domain reserved!', 'error')
            return redirect(url_for('user.dashboard'))

        try:
            # Setup the payment method
            si = stripe_checkout(current_user.email, domain)

            # Redirect to the payment page
            if si is not None:
                pm = get_payment_method(si)
                return render_template('user/reserve.html', current_user=current_user, domain=domain, si=si, email=current_user.email, pm=pm)
            else:
                flash("There was an error reserving this domain. Please try again.", 'error')
                return redirect(url_for('user.dashboard'))
        except Exception as e:
            print_traceback(e)
            flash("There was an error reserving this domain. Please try again.", 'error')
            return redirect(url_for('user.dashboard'))
    else:
        return render_template('user/dashboard.html', current_user=current_user)


@user.route('/save_reservation', methods=['GET','POST'])
@csrf.exempt
def save_reservation():
    if request.method == 'POST':
        # Save the customer's info to db on successful charge if they don't already exist
        if 'pm' in request.form and 'save-card' in request.form and 'domain' in request.form and 'customer_id' in request.form:

            pm = request.form['pm']
            save_card = request.form['save-card']
            domain = request.form['domain']
            customer_id = request.form['customer_id']

            if update_customer(pm, customer_id, save_card):
                # Create the backorder request in Dynadot
                r = backorder_request(domain)

                # Save the domain
                details = get_domain_availability(domain)
                d = save_domain(current_user.id, customer_id, pm, domain, details['expires'], pytz.utc.localize(dt.utcnow()))

                # Save the backorder to the db
                c = Customer.query.filter(Customer.customer_id == customer_id).scalar()
                create_backorder(d, c.id, current_user.id, r)

                flash('Your domain was successfully reserved!', 'success')
                return render_template('user/success.html', current_user=current_user)

    flash('There was a problem reserving your domain. Please try again.', 'error')
    return redirect(url_for('user.dashboard'))


@user.route('/saved_card_intent', methods=['GET','POST'])
@csrf.exempt
def saved_card_intent():
    if request.method == 'POST':
        # Save the customer's info to db on successful charge if they don't already exist
        if 'pm' in request.form and 'domain' in request.form and 'customer_id' in request.form:

            pm = request.form['pm']
            domain = request.form['domain']
            customer_id = request.form['customer_id']

            # Create the payment intent with the existing payment method
            if create_payment(domain, customer_id, pm):
                # Create the backorder request in Dynadot
                r = backorder_request(domain)

                # Save the domain after payment
                details = get_domain_availability(domain)
                d = save_domain(current_user.id, customer_id, pm, domain, details['expires'], pytz.utc.localize(dt.utcnow()))

                # Save the backorder to the db
                c = Customer.query.filter(Customer.customer_id == customer_id).scalar()
                create_backorder(d, c.id, current_user.id, r)

                flash('Your domain was successfully reserved!', 'success')
                return render_template('user/success.html', current_user=current_user)

    flash('There was a problem reserving your domain. Please try again.', 'error')
    return redirect(url_for('user.dashboard'))


# Purchase Available Domains -------------------------------------------------------------------
@user.route('/checkout', methods=['GET','POST'])
@csrf.exempt
def checkout():
    if request.method == 'POST':
        domain = request.form['domain']

        if db.session.query(exists().where(and_(Domain.name == domain, Domain.user_id == current_user.id, Domain.registered.is_(True)))).scalar():
            flash('You already own this domain!', 'error')
            # return redirect(url_for('user.dashboard'))
        try:
            # Secure the domain
            if register(domain) or True:
                # Setup the customer's payment method
                si = stripe_checkout(current_user.email, domain, True)

                # Redirect to the payment page
                if si is not None:
                    pm = get_payment_method(si)
                    return render_template('user/checkout.html', current_user=current_user, domain=domain, si=si, email=current_user.email, pm=pm)

            flash("There was an error buying this domain. Please try again.", 'error')
            return redirect(url_for('user.dashboard'))
        except Exception as e:
            print_traceback(e)
            flash("There was an error buying this domain. Please try again.", 'error')
            return redirect(url_for('user.dashboard'))
    else:
        flash("There was an error buying this domain. Please try again.", 'error')
        return render_template('user/dashboard.html', current_user=current_user)


@user.route('/saved_card_payment', methods=['GET','POST'])
@csrf.exempt
def saved_card_payment():
    if request.method == 'POST':
        # Save the customer's info to db on successful charge if they don't already exist
        if 'pm' in request.form and 'domain' in request.form and 'customer_id' in request.form:

            pm = request.form['pm']
            domain = request.form['domain']
            customer_id = request.form['customer_id']

            # Create the payment with the existing payment method
            if create_payment(domain, customer_id, pm, True):
                # Save the domain after payment
                details = get_domain_availability(domain)
                save_domain(current_user.id, customer_id, pm, domain, details['expires'], pytz.utc.localize(dt.utcnow()), True)

                flash('Your domain was successfully purchased!', 'success')
                return render_template('user/purchase_success.html', current_user=current_user)

    flash('There was a problem reserving your domain. Please try again.', 'error')
    return redirect(url_for('user.dashboard'))


# Success Messages -------------------------------------------------------------------
@user.route('/success', methods=['GET', 'POST'])
@csrf.exempt
def success():
    flash('Your domain was successfully reserved!', 'success')
    return render_template('user/success.html', current_user=current_user)


@user.route('/purchase_success', methods=['GET','POST'])
@csrf.exempt
def purchase_success():
    flash(Markup("Your domain was successfully purchased! You can see it in <a href='/dashboard'><span style='color:#009fff'>your dashboard</span></a>."),
          category='success')
    return render_template('user/purchase_success.html', current_user=current_user)


# Settings -------------------------------------------------------------------
@user.route('/settings', methods=['GET','POST'])
@login_required
@csrf.exempt
def settings():

    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))

    c = Customer.query.filter(Customer.user_id == current_user.id).scalar()
    card = get_card(c)

    return render_template('user/settings.html', current_user=current_user, card=card)


# Contact us -------------------------------------------------------------------
@user.route('/contact', methods=['GET','POST'])
@csrf.exempt
def contact():
    if request.method == 'POST':
        from app.blueprints.user.tasks import send_contact_us_email
        send_contact_us_email.delay(request.form['email'], request.form['message'])

        flash('Thanks for your email! You can expect a response shortly.', 'success')
        return redirect(url_for('user.dashboard'))
    return render_template('user/contact.html', current_user=current_user)
