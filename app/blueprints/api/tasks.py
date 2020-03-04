from app.app import create_celery_app, db
from app.blueprints.api.api_functions import print_traceback

celery = create_celery_app()


@celery.task()
def generate_drops():
    try:
        from app.blueprints.api.domain.download import pool_domains, park_domains
        from app.blueprints.api.domain.domain import get_dropping_domains, delete_dropping_domains, set_dropping_domains

        domains = pool_domains() # .delay()

        if domains is not None:
            delete_dropping_domains()
            set_dropping_domains(domains)

            return True
        else:
            domains = park_domains() #.delay()
            if domains is not None:
                delete_dropping_domains()
                set_dropping_domains(domains)

                return True

        return False
    except Exception as e:
        print_traceback(e)
        return False


@celery.task()
def pool_domains():
    from app.blueprints.api.domain.download import pool_domains
    pool_domains()


@celery.task()
def park_domains():
    from app.blueprints.api.domain.download import park_domains
    park_domains()