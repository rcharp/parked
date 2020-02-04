import sys
import string
import random
import requests
from app.extensions import db
from sqlalchemy import exists
from flask_login import current_app, current_user
from importlib import import_module


def signup_limits(user, plan):
    integration_limit = 5 if plan == 'hobby' else 20 if plan == 'startup' else 50 if plan == 'professional' else 99999 if plan == 'premium' else 0

    user.integrations_limit = integration_limit
    user.save()


def change_limits(user, new_plan, old_plan):
    print(new_plan)
    print(old_plan)
    integration_limit = 5 if new_plan['id'] == 'hobby' else 20 if new_plan['id'] == 'startup' else 50 if new_plan['id'] == 'professional' else 99999 if new_plan['id'] == 'premium' else 0

    if old_plan is None:
        user.integrations_limit = integration_limit
        user.save()
        return

    if new_plan['amount'] < old_plan['amount']:
        from app.blueprints.api.models.user_integrations import UserIntegration
        integrations = UserIntegration.query.filter(UserIntegration.user_id == user.id).all()

        for integration in integrations:
            integration.active = False
            integration.save()

    user.integrations_limit = integration_limit
    user.save()