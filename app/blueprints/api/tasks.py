from app.app import create_celery_app, db

celery = create_celery_app()


@celery.task()
def generate_drops():
    from app.blueprints.api.domain.download import pool_domains, park_domains

    if not pool_domains():
        park_domains()

    return
