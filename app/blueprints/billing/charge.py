import stripe
from flask import current_app, url_for, flash
from app.blueprints.api.api_functions import print_traceback

# Change to Live key when done testing
stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')
site_url = current_app.config.get('SITE_URL')


def reserve_domain(email, domain):
    try:
        from app.blueprints.user.models import User
        from app.blueprints.api.models.domains import Domain

        u = User.query.filter(User.email == email).scalar()

        session = stripe.checkout.Session.create(
            # customer=customer.id,
            customer_email=email,
            payment_method_types=['card'],
            line_items=[{
                'name': 'GetMyDomain - Reserve ' + domain,
                'description': "Reserve your domain with GetMyDomain. Your card won't be charged until we secure the domain.",
                'amount': 9900,
                'currency': 'usd',
                'quantity': 1,
            }],
            success_url=site_url + url_for('user.success', domain=domain),
            cancel_url=site_url + url_for('user.dashboard'),
        )
        return session.id
    except Exception as e:
        print_traceback(e)
        return None
