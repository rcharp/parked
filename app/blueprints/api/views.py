from flask import Blueprint, render_template, json, flash
from flask import redirect, url_for, current_app
from importlib import import_module
from app.blueprints.api.api_functions import print_traceback
from app.extensions import csrf
from flask import request
from app.blueprints.api.test import test as t

api = Blueprint('api', __name__, template_folder='templates')


@api.route('/test', methods=['GET','POST'])
@csrf.exempt
def test():
    if request.method == 'POST':
        domain = request.form['domain']

        try:
            results = t(domain)
            # print(results)
            flash("Test was successful.", 'success')
            flash("Results are: " + str(results), 'danger')
            return redirect(url_for('user.dashboard'))
        except Exception as e:
            print_traceback(e)
            flash("Test was unsuccessful.", 'error')
            return redirect(url_for('user.dashboard'))
    else:
        flash("Test wasn't run.", 'error')
        return redirect(url_for('user.dashboard'))


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