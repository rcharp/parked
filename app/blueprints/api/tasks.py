from app.app import create_celery_app, db
from app.blueprints.api.api_functions import print_traceback

celery = create_celery_app()


@celery.task()
def generate_drops():
    try:
        limit = 1000

        # Do not generate more drops if there are too many in the db
        from app.blueprints.api.models.drops import Drop
        if db.session.query(Drop).count() > limit:
            return False

        from app.blueprints.api.domain.download import pool_domains, park_domains
        from app.blueprints.api.domain.domain import get_dropping_domains, delete_dropping_domains, set_dropping_domains

        domains = pool_domains(limit)  # .delay()

        if domains is not None:
            if delete_dropping_domains():
                set_dropping_domains(domains, limit)

                return True
        else:
            domains = park_domains(limit)  # .delay()
            if domains is not None:
                if delete_dropping_domains():
                    set_dropping_domains(domains, limit)

                    return True

        return False
    except Exception as e:
        print_traceback(e)
        return False


@celery.task()
def pool_domains(limit):
    from app.blueprints.api.domain.download import pool_domains
    pool_domains(limit)


@celery.task()
def park_domains(limit):
    from app.blueprints.api.domain.download import park_domains
    park_domains(limit)
