import stripe
from flask import current_app

# Change to Live key when done testing
stripe.api_key = current_app.config.get('STRIPE_TEST_PUBLISHABLE_KEY')


def create_payment():
    intent = stripe.PaymentIntent.create(
        amount=9900,
        currency='usd',
    )

    return intent
