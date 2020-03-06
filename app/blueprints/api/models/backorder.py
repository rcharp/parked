from sqlalchemy import or_

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db


class Backorder(ResourceMixin, db.Model):

    __tablename__ = 'backorders'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    domain_name = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    pm = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    pi = db.Column(db.String(255), unique=True, index=True, nullable=True, server_default='')
    expires = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    date_available = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    active = db.Column('active', db.Boolean(), nullable=False, server_default='0')
    pending_delete = db.Column('pending_delete', db.Boolean(), nullable=False, server_default='0')
    secured = db.Column('secured', db.Boolean(), nullable=False, server_default='0')
    paid = db.Column('paid', db.Boolean(), nullable=False, server_default='0')

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                           index=True, nullable=True, primary_key=False, unique=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)
    domain = db.Column(db.Integer, db.ForeignKey('domains.id', onupdate='CASCADE', ondelete='CASCADE'),
                            index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Backorder, self).__init__(**kwargs)

    @classmethod
    def find_by_id(cls, identity):
        """
        Find an email by its message id.

        :param identity: Email or username
        :type identity: str
        :return: User instance
        """
        return Backorder.query.filter(
          (Backorder.id == identity).first())

    @classmethod
    def search(cls, query):
        """
        Search a resource by 1 or more fields.

        :param query: Search query
        :type query: str
        :return: SQLAlchemy filter
        """
        if not query:
            return ''

        search_query = '%{0}%'.format(query)
        search_chain = (Backorder.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: List of ids to be deleted
        :type ids: list
        :return: int
        """
        delete_count = 0

        for id in ids:
            backorder = Backorder.query.get(id)

            if backorder is None:
                continue

            backorder.delete()

            delete_count += 1

        return delete_count
