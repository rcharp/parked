from app.app import create_celery_app, db

celery = create_celery_app()


@celery.task()
def api_task():
    return


@celery.task()
def delete_table(table_id):
    # Delete the table

    from app.blueprints.api.models.tables import Table
    Table.query.filter(Table.id == table_id).delete()
    db.session.commit()
