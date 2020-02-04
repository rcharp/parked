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
from lib.airtable_wrapper.airtable.airtable import Airtable
from app.extensions import cache, csrf, timeout, db
from importlib import import_module
from sqlalchemy import or_, and_, exists
from app.blueprints.api.api_functions import print_traceback
from app.blueprints.api.models.bases import Base
from app.blueprints.api.models.app_auths import AppAuthorization

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

    # Get settings trial information
    trial_days_left = -1
    if not current_user.subscription and not current_user.trial and current_user.role == 'member':
        flash(Markup("Your free trial has expired. Please <a href='/subscription/update'>sign up</a> for a plan to continue."), category='error')

    if current_user.trial and current_user.role == 'member':
        trial_days_left = 14 - (datetime.datetime.now() - current_user.created_on.replace(tzinfo=None)).days

    if trial_days_left < 0:
        current_user.trial = False
        current_user.save()

    from app.blueprints.api.models.bases import Base
    from app.blueprints.api.models.tables import Table

    tables = Table.query.filter(Table.user_id == current_user.id).all()
    bases = Base.query.filter(Base.user_id == current_user.id).all()
    keys = AppAuthorization.query.filter(AppAuthorization.user_id == current_user.id).all()

    return render_template('user/dashboard.html', current_user=current_user, bases=bases, tables=tables, keys=keys)


# Forms and Bases -------------------------------------------------------------------
@user.route('/new_form', methods=['GET','POST'])
@login_required
@csrf.exempt
def new_form():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))

    # Get settings trial information
    trial_days_left = -1
    if not current_user.subscription and not current_user.trial and current_user.role == 'member':
        flash(Markup("Your free trial has expired. Please <a href='/subscription/update'>sign up</a> for a plan to continue."), category='error')

    if current_user.trial and current_user.role == 'member':
        trial_days_left = 14 - (datetime.datetime.now() - current_user.created_on.replace(tzinfo=None)).days

    if trial_days_left < 0:
        current_user.trial = False
        current_user.save()

    bases = Base.query.filter(Base.user_id == current_user.id).all()

    return render_template('user/new_form.html', current_user=current_user, bases=bases)


@user.route('/connect_base', methods=['GET','POST'])
@csrf.exempt
def connect_base():
    if request.method == 'POST':
        try:
            from app.blueprints.api.models.bases import Base
            if 'new-base' in request.form and request.form['new-base']:
                if db.session.query(exists().where(Base.base_id == request.form['new-base'])).scalar():
                    flash("This base has already been added. Please try again.", 'error')
                    return redirect(url_for('user.new_form'))
                else:
                    auth = AppAuthorization.query.filter(AppAuthorization.user_id == current_user.id).scalar()

                    b = Base()
                    b.user_id = current_user.id
                    b.base_id = request.form['new-base']
                    b.api_key = auth.api_key

                    b.save()

                    flash('Your base has been successfully added! Please select one from the list.', 'success')
                    return redirect(url_for('user.new_form'))

            elif 'existing-base' in request.form:
                from app.blueprints.api.models.tables import Table
                tables = Table.query.filter(and_(Table.user_id == current_user.id), Table.base_id == request.form['existing-base']).all()
                return render_template('user/connect_table.html', base=request.form['existing-base'], tables=tables)
            else:
                flash('Please select an existing base or add a new one.', 'error')
                return redirect(url_for('user.new_form'))

        except Exception as e:
            print_traceback(e)
            flash('There was an error adding your base. Please try again.', 'error')

        return redirect(url_for('user.dashboard'))


@user.route('/add_base', methods=['POST'])
@csrf.exempt
def add_base():
    if request.method == 'POST':
        try:
            if 'base-id' in request.form and 'api-key' in request.form:

                if db.session.query(exists().where(and_(Base.base_id == request.form['base-id'], Base.api_key == request.form['api-key']))).scalar():
                    flash("This account is already in use. Please try again.", 'error')
                else:
                    auth = AppAuthorization.query.filter(AppAuthorization.api_key == request.form['api-key']).scalar()
                    if auth is None:
                        a = AppAuthorization()
                        a.user_id = current_user.id
                        a.api_key = request.form['api-key']
                        a.save()

                    if db.session.query(exists().where(AppAuthorization.api_key == request.form['api-key'])).scalar():
                        b = Base()
                        b.user_id = current_user.id
                        b.base_id = request.form['base-id']
                        b.api_key = request.form['api-key']

                        b.save()

                        flash('Your base has been successfully added!', 'success')

        except Exception as e:
            print_traceback(e)
            flash('There was an error adding your base. Please try again.', 'error')

        return redirect(url_for('user.dashboard'))


@user.route('/connect_table', methods=['GET','POST'])
@csrf.exempt
def connect_table():
    from app.blueprints.api.models.tables import Table
    if request.method == 'POST':
        try:
            from app.blueprints.api.models.bases import Base

            if 'table-name' in request.form and request.form['table-name'] and 'base-id' in request.form and request.form['base-id']:
                if db.session.query(exists().where(and_(Table.base_id == request.form['base-id'], Table.table_name == request.form['table-name']))).scalar():
                    flash("This table has already been added for this base. Please try again.", 'error')
                else:

                    t = Table()
                    t.user_id = current_user.id
                    t.base_id = request.form['base-id']
                    t.table_name = request.form['table-name']

                    t.save()

                    flash('Your table has been successfully added! Please select one from the list.', 'success')

            elif 'existing-table' in request.form:
                from app.blueprints.api.api_functions import get_table

                table = Table.query.filter(and_(Table.table_name == request.form['existing-table']), Table.user_id == current_user.id).scalar()
                base_id = table.base_id

                from app.blueprints.api.models.app_auths import AppAuthorization
                auth = AppAuthorization.query.filter(AppAuthorization.user_id == current_user.id).scalar()
                api_key = auth.api_key

                t, columns = get_table(request.form['existing-table'], base_id, api_key)

                if columns is not None and t is not None:
                    return render_template('user/create_form.html', table_name=request.form['existing-table'], columns=columns, base=base_id, table=t)
                else:
                    flash("That table wasn't found on this base. Please select another one.", 'error')
                    tables = Table.query.filter(and_(Table.user_id == current_user.id), Table.base_id == request.form['base-id']).all()
                    return render_template('user/connect_table.html', base=request.form['base-id'], tables=tables)
            else:
                flash('Please select an existing table or add a new one.', 'error')

                tables = Table.query.filter(and_(Table.user_id == current_user.id), Table.base_id == request.form['base-id']).all()
                return render_template('user/connect_table.html', base=request.form['base-id'], tables=tables)
        except Exception as e:
            print_traceback(e)
            flash('There was an error adding your table. Please try again.', 'error')
            return redirect(url_for('user.dashboard'))

    tables = Table.query.filter(and_(Table.user_id == current_user.id), Table.base_id == request.args.get('base_id')).all()
    return render_template('user/connect_table.html', base=request.args.get('base_id'), tables=tables)


@user.route('/add_table', methods=['POST'])
@csrf.exempt
def add_table():
    if request.method == 'POST':
        try:
            from app.blueprints.api.models.tables import Table
            if 'table-name' in request.form:
                if db.session.query(exists().where(and_(Table.base_id == request.form['base-id'], Table.table_name == request.form['table-name']))).scalar():
                    flash("This table has already been added. Please try again.", 'error')
                else:
                    from app.blueprints.api.models.tables import Table
                    from app.blueprints.api.models.app_auths import AppAuthorization

                    auth = AppAuthorization.query.filter(AppAuthorization.user_id == current_user.id).scalar()
                    api_key = auth.api_key

                    columns = get_table(request.form['table-name'], request.form['table-name'], api_key)

                    if columns is not None:

                        t = Table()
                        t.user_id = current_user.id
                        t.base_id = request.form['base-id']
                        t.table_name = request.form['table-name']

                        t.save()

                        flash('Your base has been successfully added!', 'success')
                    else:
                        flash("This table wasn't found on this base. Please try again.", 'error')

        except Exception as e:
            print_traceback(e)
            flash('There was an error adding this table. Please try again.', 'error')

        return render_template('user/connect_table.html', base=request.form['base-id'])


@user.route('/create_form', methods=['POST'])
@login_required
@csrf.exempt
def create_form():
    from app.blueprints.api.models.tables import Table

    if request.method == 'POST':
        try:
            from app.blueprints.api.models.bases import Base

            if 'table-name' in request.form and request.form['table-name']:
                tables = Table.query.filter(and_(Table.user_id == current_user.id),
                                        Table.base_id == request.form['base-id']).all()
                return render_template('user/connect_table.html', base=request.form['base-id'], tables=tables)
        except Exception as e:
            print_traceback(e)
            flash('There was an error adding your table. Please try again.', 'error')

        return redirect(url_for('user.dashboard'))


# Used for the integrations list on the dashboard. Delete the integration when the X is clicked.
@user.route('/delete_table/<table_id>', methods=['GET','POST'])
@login_required
@csrf.exempt
def delete_table(table_id):
    try:
        from app.blueprints.api.api_functions import delete_table

        # Delete the integration
        delete_table(table_id)

        flash('Table has been deleted.', 'success')
    except Exception as e:
        print(e)
        flash('There was a problem deleting this table. Please try again.', 'error')
    return redirect(url_for('user.dashboard'))


# Settings -------------------------------------------------------------------
@user.route('/settings', methods=['GET','POST'])
@login_required
@csrf.exempt
def settings():

    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))

    # Get settings trial information
    trial_days_left = -1
    if not current_user.subscription and not current_user.trial and current_user.role == 'member':
        flash(Markup("Your free trial has expired. Please <a href='/subscription/update'>sign up</a> for a plan to continue."), category='error')

    if current_user.trial and current_user.role == 'member':
        trial_days_left = 14 - (datetime.datetime.now() - current_user.created_on.replace(tzinfo=None)).days

    if trial_days_left < 0:
        current_user.trial = False
        current_user.save()

    return render_template('user/settings.html', current_user=current_user, trial_days_left=trial_days_left)


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


@user.route('/auth/<app>')
@login_required
@csrf.exempt
def auth(app):
    try:
        module = import_module("app.blueprints.api.apps." + app + '.' + app)
        account = module.account()

        flash("Successfully connected to your account.", 'success')
        return render_template('user/auth.html', app=app, account=account)
    except Exception as e:
        print_traceback(e)
        flash("There was an error connecting to this app. Please try again.", 'error')
        return redirect(url_for('user.dashboard'))


@user.route('/update_send_failure_email', methods=['POST'])
@csrf.exempt
def update_send_failure_email():
    if request.method == 'POST':
        try:
            if 'checked' in request.form:
                if request.form['checked'] == 'true':
                    current_user.send_failure_email = True
                else:
                    current_user.send_failure_email = False

                current_user.save()
                return jsonify({'success': {}})

        except Exception as e:
            print_traceback(e)
    return None


@user.route('/run_tests', methods=['GET','POST'])
@login_required
@csrf.exempt
def run_tests():

    try:
        from app.blueprints.api.api_tests import run_tests as run
        run()
    except Exception as e:
        print_traceback(e)
        pass

    return redirect(url_for('user.dashboard'))


@user.route('/colorlib', methods=['GET','POST'])
@csrf.exempt
def colorlib():

    return render_template('user/colorlib.html', current_user=current_user)
