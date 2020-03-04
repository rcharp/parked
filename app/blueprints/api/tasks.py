from app.app import create_celery_app, db

celery = create_celery_app()


@celery.task()
def generate_drops():
    from app.blueprints.api.domain.download import pool_domains, park_domains
    from app.blueprints.api.domain.domain import get_dropping_domains, delete_dropping_domains, set_dropping_domains

    # Check the DB to see if we have drops already
    # If so, clear them out and get new ones
    drops = get_dropping_domains()
    if drops is not None and len(drops) < 0:

        domains = pool_domains()

        if domains is not None:
            delete_dropping_domains()
            set_dropping_domains(domains)
        else:
            domains = park_domains()
            if domains is not None:
                delete_dropping_domains()
                set_dropping_domains(domains)

    return
