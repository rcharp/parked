import stripe
from flask import current_app, url_for
from app.blueprints.api.api_functions import print_traceback
from app.blueprints.billing.models.customer import Customer
from app.blueprints.api.models.domains import Domain
from sqlalchemy import exists, and_
from app.extensions import db


def stripe_checkout(email, domain):
    try:
        from app.blueprints.user.models import User
        from app.blueprints.api.models.domains import Domain
        from app.blueprints.billing.models.customer import Customer

        # Get the current user
        u = User.query.filter(User.email == email).scalar()

        # Create the Stripe customer if they don't already exist
        if not db.session.query(exists().where(Customer.user_id == u.id)).scalar():
            c = Customer()
            c.user_id = u.id
            c.email = email
            c.save()

        # Change to Live key when done testing
        stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')
        site_url = current_app.config.get('SITE_URL')

        session = create_session(email, site_url, domain)
        return session.id
    except Exception as e:
        print_traceback(e)
        return None


def create_session(email, site_url, domain):
    return stripe.checkout.Session.create(
        customer_email=email,
        payment_method_types=['card'],
        line_items=[{
            'name': 'GetMyDomain - Reserve ' + domain,
            'description': "Reserve your domain with GetMyDomain. Your card won't be charged until we secure the domain.",
            'amount': 9900,
            'currency': 'usd',
            'quantity': 1,
        }],
        success_url=site_url + url_for('user.success', domain=domain) + '&session_id={CHECKOUT_SESSION_ID}',
        cancel_url=site_url + url_for('user.dashboard'),
    )


def setup_intent():
    stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')
    return stripe.SetupIntent.create()


def update_customer(session_id, domain, user_id):
    try:
        # Change to Live key when done testing
        stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')

        # Get and update the customer in the database to have the Stripe customer ID
        session = stripe.checkout.Session.retrieve(session_id)
        session_customer = session.customer

        customer = stripe.Customer.retrieve(session_customer)

        # Get the customer and update its ID
        c = Customer.query.filter(Customer.email == customer.email).scalar()
        c.customer_id = customer.id
        c.save()

        # Update the domain and add the Stripe customer ID to it
        d = Domain.query.filter(and_(Domain.user_id == user_id), Domain.name == domain).scalar()
        d.customer_id = customer.id
        d.save()

        return True
    except Exception as e:
        print_traceback(e)
        return False
