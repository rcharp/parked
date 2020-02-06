import stripe
from flask import current_app, url_for
from app.blueprints.api.api_functions import print_traceback
from sqlalchemy import exists
from app.extensions import db

site_url = current_app.config.get('SITE_URL')


def stripe_checkout(email, domain):
    try:
        from app.blueprints.user.models import User
        from app.blueprints.api.models.domains import Domain
        from app.blueprints.billing.models.customer import Customer

        # Get the current user
        u = User.query.filter(User.email == email).scalar()

        # Create the Stripe customer if they don't already exist
        if not db.session.query(exists().where(Customer.id == u.payment_id)).scalar():
            c = Customer()
            c.user_id = u.id
            c.email = email
            c.save()

        # Change to Live key when done testing
        stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')

        session = stripe.checkout.Session.create(
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
        return session.id
    except Exception as e:
        print_traceback(e)
        return None


def update_customer(session_id, domain):
    # Change to Live key when done testing
    stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')

    session = stripe.checkout.Session.retrieve(session_id)
    customer = session.customer

    print(customer)
