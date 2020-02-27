import datetime

import pytz

from config import settings
from lib.util_sqlalchemy import ResourceMixin
from app.extensions import db
from app.blueprints.billing.gateways.stripecom import Card as PaymentCard
from app.blueprints.billing.gateways.stripecom import \
    Customer as PaymentCustomer


class Customer(ResourceMixin, db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                        index=True, unique=True, nullable=False)

    # Customer details.
    customer_id = db.Column(db.String(128))
    name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    save_card = db.Column('save_card', db.Boolean(), nullable=False, server_default='0')

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Customer, self).__init__(**kwargs)

    def create(self, user=None, name=None, token=None):
        """
        Create a new customer.

        :param user: User to apply the customer to
        :type user: User instance
        :param name: User's billing name
        :type name: str
        :param token: Token returned by JavaScript
        :type token: str
        :return: bool
        """
        if token is None:
            return False

        customer = PaymentCustomer.create(token=token,
                                          email=user.email,
                                          name=user.name)

        # Update the user account.
        user.payment_id = customer.id
        user.name = name
        user.cancelled_customer_on = None

        # Set the customer details.
        self.user_id = user.id

        db.session.add(user)
        db.session.add(self)

        db.session.commit()

        return True

    def update(self, user=None, name=None, email=None):
        """
        Update an existing customer.

        :param user: User to apply the customer to
        :type user: User instance
        :param coupon: Coupon code to apply
        :type coupon: str
        :param plan: Plan identifier
        :type plan: str
        :return: bool
        """
        PaymentCustomer.update(user.payment_id, name, email)

        db.session.add(user.customer)
        db.session.commit()

        return True

    def cancel(self, user=None, discard_credit_card=True):
        """
        Cancel an existing customer.

        :param user: User to apply the customer to
        :type user: User instance
        :param discard_credit_card: Delete the user's credit card
        :type discard_credit_card: bool
        :return: bool
        """
        PaymentCustomer.cancel(user.payment_id)

        user.payment_id = None
        user.cancelled_customer_on = datetime.datetime.now(pytz.utc)

        db.session.add(user)
        db.session.delete(user.customer)

        # Explicitly delete the credit card because the FK is on the
        # user, not customer so we can't depend on cascading deletes.
        # This is for cases where you may want to keep a user's card
        # on file even if they cancelled.
        if discard_credit_card:
            db.session.delete(user.credit_card)

        db.session.commit()

        return True

    def update_payment_method(self, user=None, credit_card=None,
                              name=None, token=None):
        """
        Update the customer.

        :param user: User to modify
        :type user: User instance
        :param credit_card: Card to modify
        :type credit_card: Credit Card instance
        :param name: User's billing name
        :type name: str
        :param token: Token returned by JavaScript
        :type token: str
        :return: bool
        """
        if token is None:
            return False

        return True
