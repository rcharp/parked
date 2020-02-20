import stripe
from flask import current_app, url_for
from app.blueprints.api.api_functions import print_traceback, generate_id
from app.blueprints.billing.models.customer import Customer
from app.blueprints.api.models.domains import Domain
from sqlalchemy import exists, and_
from app.extensions import db


site_name = "GetParked.io"


def stripe_checkout(email, domain, purchase=False):
    try:
        from app.blueprints.user.models import User
        from app.blueprints.api.models.domains import Domain
        from app.blueprints.billing.models.customer import Customer

        # Get the current user
        u = User.query.filter(User.email == email).scalar()

        # Create the Stripe customer if they don't already exist
        if not db.session.query(exists().where(Customer.user_id == u.id)).scalar():
            customer_id = create_customer(u, email)
        else:
            # If they do exist, get the customer's ID
            c = Customer.query.filter(Customer.user_id == u.id).scalar()
            customer_id = c.customer_id

            # Make sure the customer exists in Stripe. If not, delete it from the db
            stripe_customer = stripe.Customer.retrieve(customer_id)

            if stripe_customer is None or 'deleted' in stripe_customer and stripe_customer.deleted:
                c.delete()

                # After deleting the old customer from the db, update the old domains for this customer
                domains = Domain.query.filter(Domain.customer_id == customer_id).all()

                # Create a new customer in the DB
                customer_id = create_customer(u, email)

                # Update the domains to have the new customer ID
                for domain in domains:
                    domain.customer_id = customer_id
                    domain.save()

            elif customer_id is None:
                customer_id = create_customer(u, email, False)

        if customer_id is not None:
            if purchase:
                p = create_payment(domain, customer_id)
                return p
            else:
                si = setup_intent(domain, customer_id)
                return si
    except Exception as e:
        print_traceback(e)
        return None


def create_payment(domain, customer_id, pm=None, confirm=False):
    stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')

    description = "Buy " + domain + " from " + site_name + "." if confirm \
        else "Reserve " + domain + " with " + site_name + " for $99. Your card won't be charged until we secure the domain."

    if pm is not None:
        return stripe.PaymentIntent.create(
            amount=9900,
            customer=customer_id,
            payment_method=pm,
            confirm=confirm,
            currency="usd",
            description=description,
            payment_method_types=["card"],
        )
    else:
        return stripe.PaymentIntent.create(
            amount=9900,
            customer=customer_id,
            confirm=confirm,
            currency="usd",
            description=description,
            payment_method_types=["card"],
        )


def confirm_payment(domain):
    stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')
    return stripe.PaymentIntent.create(
        amount=9900,
        currency="usd",
        description="Reserve " + domain + " with " + site_name + ". Your card won't be charged until we secure the domain.",
        payment_method_types=["card"]
    )


def charge_card(domain):
    stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')
    return stripe.PaymentIntent.create(
        amount=9900,
        confirm="True",
        currency="usd",
        description="Buy " + domain + " from " + site_name + ".",
        payment_method_types=["card"],
    )


# Create the customer
def create_customer(u, email, create_db=True):

    # Create the customer in Stripe
    stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')
    customer = stripe.Customer.create(
        email=email
    )

    # Create the customer in the database
    if create_db:
        c = Customer()
        c.user_id = u.id
        c.email = email
        c.customer_id = customer.id
        c.save()

    return customer.id


def setup_intent(domain, customer_id):
    try:
        stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')

        c = Customer.query.filter(Customer.customer_id == customer_id).scalar()
        if c is not None and c.save_card:
            # Get the default payment method and use that
            customer = stripe.Customer.retrieve(customer_id)
            pm = customer.default_source

            if pm is not None:
                return stripe.SetupIntent.create(
                    customer=customer_id,
                    description="Reserve " + domain + " with " + site_name + ". Your card won't be charged until we secure the domain.",
                    payment_method_types=["card"],
                    payment_method=pm,
                )
            else:
                return stripe.SetupIntent.create(
                    customer=customer_id,
                    description="Reserve " + domain + " with " + site_name + ". Your card won't be charged until we secure the domain.",
                    payment_method_types=["card"],
                )
        else:
            return stripe.SetupIntent.create(
                customer=customer_id,
                description="Reserve " + domain + " with " + site_name + ". Your card won't be charged until we secure the domain.",
                payment_method_types=["card"],
            )
    except Exception as e:
        print_traceback(e)
        return None


def confirm_intent(si, pm):
    try:
        stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')
        return stripe.SetupIntent.confirm(
            si,
            payment_method=pm,
        )
    except Exception as e:
        print_traceback(e)
        return None


def create_session(email, site_url, domain):
    return stripe.checkout.Session.create(
        customer_email=email,
        payment_method_types=['card'],
        line_items=[{
            'name': site_name + ' - Reserve ' + domain,
            'description': "Reserve your domain with " + site_name + ". Your card won't be charged until we secure the domain.",
            'amount': 9900,
            'currency': 'usd',
            'quantity': 1,
        }],
        success_url=site_url + url_for('user.success', domain=domain) + '&session_id={CHECKOUT_SESSION_ID}',
        cancel_url=site_url + url_for('user.dashboard'),
    )


def update_customer(pm, customer_id, save_card):
    try:
        # Change to Live key when done testing
        stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')

        payment_method = stripe.PaymentMethod.retrieve(pm)

        if payment_method.customer is None:
            # Get and update the customer in Stripe with the payment method
            stripe.PaymentMethod.attach(
                pm,
                customer=customer_id,
            )

        if save_card == 'true':
            stripe.Customer.modify(
                customer_id,
                invoice_settings={'default_payment_method':pm}
            )

            customer = Customer.query.filter(Customer.customer_id == customer_id).scalar()
            customer.save_card = True
            customer.save()

        return True

    except Exception as e:
        print_traceback(e)
        return False


def delete_payment(order_id):
    try:
        stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')
        return stripe.PaymentIntent.cancel(
            order_id
        )
    except Exception as e:
        print_traceback(e)
        return None


def get_payment_method(si):
    stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')

    pm = None
    c = Customer.query.filter(Customer.customer_id == si.customer).scalar()
    if c.save_card:
        customer = stripe.Customer.retrieve(c.customer_id)
        pm = stripe.PaymentMethod.retrieve(customer.invoice_settings.default_payment_method)

    return pm


def get_card(c):
    stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')

    if c is None:
        return None

    pm = None
    if c.save_card:
        customer = stripe.Customer.retrieve(c.customer_id)
        pm = stripe.PaymentMethod.retrieve(customer.invoice_settings.default_payment_method)

    return pm
