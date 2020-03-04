from app.app import create_celery_app, db

celery = create_celery_app()


@celery.task()
def generate_drops():
    from app.blueprints.api.domain.download import pool_domains, park_domains
    from app.blueprints.api.domain.domain import get_dropping_domains, delete_dropping_domains, set_dropping_domains

    domains = pool_domains()

    if domains is not None:
        delete_dropping_domains()
        set_dropping_domains(domains)

        return True
    else:
        domains = park_domains()
        if domains is not None:
            delete_dropping_domains()
            set_dropping_domains(domains)

            return True

    return False


@celery.task()
def pool_domains():
    from app.blueprints.api.domain.download import pool_domains
    pool_domains()


@celery.task()
def park_domains():
    from app.blueprints.api.domain.download import park_domains
    park_domains()