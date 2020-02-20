from sqlalchemy import or_

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db


class SearchedDomain(ResourceMixin, db.Model):

    __tablename__ = 'searched_domains'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')
    expires = db.Column(db.String(255), unique=False, index=True, nullable=True, server_default='')

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                           index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(SearchedDomain, self).__init__(**kwargs)

    @classmethod
    def find_by_id(cls, identity):
        """
        Find an email by its message id.

        :param identity: Email or username
        :type identity: str
        :return: User instance
        """
        return SearchedDomain.query.filter(
          (SearchedDomain.id == identity).first())

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
        search_chain = (SearchedDomain.id.ilike(search_query))

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
            searched_domain = SearchedDomain.query.get(id)

            if searched_domain is None:
                continue

            searched_domain.delete()

            delete_count += 1

        return delete_count
