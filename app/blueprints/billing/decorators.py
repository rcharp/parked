from functools import wraps

import stripe
from flask import redirect, url_for, flash
from flask_login import current_user


def subscription_required(f):
    """
    Ensure a user is subscribed, if not redirect them to the pricing table.

    :return: Function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.customer:
            return redirect(url_for('billing.pricing'))

        return f(*args, **kwargs)

    return decorated_function


def handle_stripe_exceptions(f):
    """
    Handle Stripe exceptions so they do not throw 500s.

    :param f:
    :type f: Function
    :return: Function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except stripe.error.CardError:
            flash('Sorry, your card was declined. Try again perhaps?', 'error')
            return redirect(url_for('user.dashboard'))
        except stripe.error.InvalidRequestError as e:
            flash(e, 'error')
            return redirect(url_for('user.dashboard'))
        except stripe.error.AuthenticationError as e:
            flash('Authentication with Stripe failed. Please try again later.', 'error')
            return redirect(url_for('user.dashboard'))
        except stripe.error.APIError as e:
            flash('There was an error while connecting to Stripe. Please try again.', 'error')
            return redirect(url_for('user.dashboard'))
        except stripe.error.APIConnectionError:
            flash(
                'Our payment gateway is experiencing connectivity issues'
                ', please try again.', 'error')
            return redirect(url_for('user.dashboard'))
        except stripe.error.StripeError:
            flash(
                'Our payment gateway is having issues, please try again.',
                'error')
            return redirect(url_for('user.dashboard'))

    return decorated_function
