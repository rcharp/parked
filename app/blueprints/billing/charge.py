import stripe
from flask import current_app

# Change to Live key when done testing
stripe.api_key = current_app.config.get('STRIPE_TEST_PUBLISHABLE_KEY')


def purchase_domain(customer, domain):
  stripe.Charge.create(
    amount=9900,
    currency="usd",
    source="tok_visa",
    description="My First Test Charge (created for API docs)",
  )