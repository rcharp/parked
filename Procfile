web: gunicorn -c "python:config.gunicorn" --reload "app.app:create_app()"
worker: celery -A app.blueprints.user.tasks worker -l info --loglevel=INFO --concurrency 1
# webhook: celery -A app.blueprints.billing.webhooks worker -B -l info --without-gossip --without-mingle --without-heartbeat --loglevel=INFO --concurrency 1