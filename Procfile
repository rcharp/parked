web: gunicorn -c "python:config.gunicorn" --reload "app.app:create_app()" --loglevel=debug --timeout=120
worker: celery -A app.blueprints.user.tasks worker -l info --loglevel=debug --concurrency 1
api: celery -A app.blueprints.api.tasks worker -B -l info --without-gossip --without-mingle --without-heartbeat --loglevel=debug --concurrency 1