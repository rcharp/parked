import stripe
from flask import current_app, url_for
from app.blueprints.api.api_functions import print_traceback, generate_id
from app.blueprints.billing.models.customer import Customer
from app.blueprints.api.models.domains import Domain
from sqlalchemy import exists, and_
from app.extensions import db
from decimal import Decimal
import time


site_name = "GetParked.io"


# The main checkout function for charging a user's card. Used for both reserving and purchasing a domain.
def stripe_checkout(email, domain, price, purchase=False):
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
            # Sleep for a sec to give Stripe's API a chance to catch up
            time.sleep(1)
            # The customer is buying the domain outright
            if purchase:
                p = create_payment(domain, price, customer_id, None, True)
                return p
            # The customer is setting up a card for a reservation
            else:
                si = setup_intent(domain, customer_id)
                # si = create_payment(domain, price, customer_id, None, False, False)
                return si
    except Exception as e:
        print_traceback(e)
        return None


# Either purchase or setup a PaymentIntent for the customer's card.
# Used by the stripe_checkout function above
def create_payment(domain, price, customer_id, pm=None, purchase=False, confirm=False):
    stripe.api_key = current_app.config.get('STRIPE_KEY')
    price = int(float(price) * 100) if price is not None else 9900

    description = "Buy " + domain + " from " + site_name + "." if confirm or purchase \
        else "Reserve " + domain + " with " + site_name + " for $99. Your card won't be charged until we secure the domain."

    # If pm is not None then the user already has a card on file
    if pm is not None:
        return stripe.PaymentIntent.create(
            amount=price,
            customer=customer_id,
            payment_method=pm,
            confirm=confirm,
            currency="usd",
            description=description,
            payment_method_types=["card"],
        )
    else:
        return stripe.PaymentIntent.create(
            amount=price,
            customer=customer_id,
            confirm=confirm,
            currency="usd",
            description=description,
            payment_method_types=["card"],
        )


# Create the customer in both Stripe and the database
def create_customer(u, email, create_db=True):

    # Create the customer in Stripe
    stripe.api_key = current_app.config.get('STRIPE_KEY')
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


# Setup the PaymentIntent for the reservation
def setup_intent(domain, customer_id):
    try:
        stripe.api_key = current_app.config.get('STRIPE_KEY')

        # Get the customer from the db if they exist
        c = Customer.query.filter(Customer.customer_id == customer_id).scalar()

        # If the customer has a card on file, get the default payment method and use that
        if c is not None and c.save_card:

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


# Charge the user's card for the reservation, if the domain is secured.
# TODO: Implement the functionality for calling this when the domain is secured
def confirm_intent(si, pm):
    try:
        stripe.api_key = current_app.config.get('STRIPE_KEY')
        return stripe.SetupIntent.confirm(
            si,
            payment_method=pm,
        )
    except Exception as e:
        print_traceback(e)
        return None


def confirm_payment(pi, pm):
    try:
        stripe.api_key = current_app.config.get('STRIPE_KEY')
        return stripe.PaymentIntent.confirm(
            pi,
            payment_method=pm
        )
    except Exception as e:
        print_traceback(e)
        return None


# Update the customer in Stripe and the db, as well as their card info
def update_customer(pm, customer_id, save_card):
    try:
        # Change to Live key when done testing
        stripe.api_key = current_app.config.get('STRIPE_KEY')

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


# Delete the payment intent when the user cancels a reservation
# TODO: Implement the functionality to delete the payment in Stripe
def delete_payment(order_id):
    try:
        stripe.api_key = current_app.config.get('STRIPE_KEY')
        # return stripe.PaymentIntent.cancel(
        #     order_id
        # )
        return stripe.SetupIntent.cancel(
            order_id
        )
    except Exception as e:
        print_traceback(e)
        return None


# Gets the customer's payment method from Stripe
def get_payment_method(si):
    stripe.api_key = current_app.config.get('STRIPE_KEY')

    pm = None
    c = Customer.query.filter(Customer.customer_id == si.customer).scalar()
    if c.save_card:
        customer = stripe.Customer.retrieve(c.customer_id)
        pm = stripe.PaymentMethod.retrieve(customer.invoice_settings.default_payment_method)

    return pm


# Get's the customer's card info from Stripe. Used to display the last 4 digits on the settings/checkout pages
def get_card(c):
    stripe.api_key = current_app.config.get('STRIPE_KEY')

    if c is None:
        return None

    pm = None
    if c.save_card:
        customer = stripe.Customer.retrieve(c.customer_id)
        pm = stripe.PaymentMethod.retrieve(customer.invoice_settings.default_payment_method)

    return pm


# Not used yet -----------------------------------------------------------------
# Confirm an existing payment
# Not currently used
# def confirm_payment(domain):
#     stripe.api_key = current_app.config.get('STRIPE_KEY')
#     return stripe.PaymentIntent.create(
#         amount=9900,
#         currency="usd",
#         description="Reserve " + domain + " with " + site_name + ". Your card won't be charged until we secure the domain.",
#         payment_method_types=["card"]
#     )


# Charge the user's card for the immediate payment
# Not currently used
# def confirm_payment_intent(domain, pi, pm):
#     stripe.api_key = current_app.config.get('STRIPE_KEY')
#     return stripe.PaymentIntent.confirm(
#         pi,
#         payment_method=pm
#     )


# Old code to create a session for payments. Not currently used.
# def create_session(email, site_url, domain):
#     return stripe.checkout.Session.create(
#         customer_email=email,
#         payment_method_types=['card'],
#         line_items=[{
#             'name': site_name + ' - Reserve ' + domain,
#             'description': "Reserve your domain with " + site_name + ". Your card won't be charged until we secure the domain.",
#             'amount': 9900,
#             'currency': 'usd',
#             'quantity': 1,
#         }],
#         success_url=site_url + url_for('user.success', domain=domain) + '&session_id={CHECKOUT_SESSION_ID}',
#         cancel_url=site_url + url_for('user.dashboard'),
#     )

