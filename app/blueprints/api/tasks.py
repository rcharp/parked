from app.app import create_celery_app, db

celery = create_celery_app()


@celery.task()
def generate_drops():
    from app.blueprints.api.domain.domain import generate_drops
    generate_drops()


@celery.task()
def order_domains():
    from app.blueprints.api.domain.dynadot import order_domains
    order_domains()


@celery.task()
def retry_charges():
    from app.blueprints.api.domain.domain import retry_charges
    retry_charges()


@celery.task()
def pool_domains(limit):
    from app.blueprints.api.domain.download import pool_domains
    pool_domains(limit)


@celery.task()
def park_domains(limit):
    from app.blueprints.api.domain.download import park_domains
    park_domains(limit)
