from flask import Blueprint, render_template, json, flash
from flask import redirect, url_for, current_app
from importlib import import_module
from app.blueprints.api.api_functions import print_traceback

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
