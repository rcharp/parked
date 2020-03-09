from datetime import timedelta
import os
from celery.schedules import crontab
from app.blueprints.api.domain.domain import get_backorder_count

SITE_NAME = 'getparked.io'

PRODUCTION = True

DEBUG = True
LOG_LEVEL = 'DEBUG'  # CRITICAL / ERROR / WARNING / INFO / DEBUG

SECRET_KEY = os.environ.get('SECRET_KEY', None)
CRYPTO_KEY = os.environ.get('CRYPTO_KEY', None)
PASSWORD = os.environ.get('PASSWORD', None)

# Flask-Mail.
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None)
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None)
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', None)
MAIL_SERVER = os.environ.get('MAIL_SERVER', None)
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True

CARD_NAME = ''
CARD_NUMBER = ''
CARD_MONTH = ''
CARD_YEAR = ''
CARD_CVV = ''

# Cache
CACHE_TYPE = 'redis'
CACHE_REDIS_HOST = os.environ.get('REDIS_HOST', None)
CACHE_REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
CACHE_DEFAULT_TIMEOUT = os.environ.get('DEFAULT_TIMEOUT', None)
CACHE_REDIS_PORT = os.environ.get('REDIS_PORT', None)
CACHE_REDIS_URL = os.environ.get('REDIS_URL', None)

# Celery Heartbeat.
BROKER_HEARTBEAT = 10
BROKER_HEARTBEAT_CHECKRATE = 2

# Celery.
CLOUDAMQP_URL = os.environ.get('CLOUDAMQP_URL', None)
REDIS_URL = os.environ.get('REDIS_URL', None)
REDBEAT_REDIS_URL = os.environ.get('REDIS_URL', None)

CELERY_BROKER_URL = os.environ.get('REDIS_URL', None)
CELERY_BROKER_HEARTBEAT = 10
CELERY_BROKER_HEARTBEAT_CHECKRATE = 2
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', None)
CELERY_REDIS_URL = os.environ.get('REDIS_URL', None)
CELERY_REDIS_HOST = os.environ.get('REDIS_HOST', None)
CELERY_REDIS_PORT = os.environ.get('REDIS_PORT', None)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_EXPIRES = 300
CELERY_REDIS_MAX_CONNECTIONS = 20
CELERY_TASK_FREQUENCY = 2  # How often (in minutes) to run this task
backorder_count = get_backorder_count()
CELERYBEAT_SCHEDULE = {
    'dropping_domains': {
        'task': 'app.blueprints.api.tasks.generate_drops',
        # 'schedule': crontab(minute=0, hour="*/1") # every hour
        # 'schedule': crontab(minute="*/1") # every minute
        # 'schedule': crontab(minute="*/5") # every 5 minutes
        'schedule': crontab(hour=0, minute=0) # every night at midnight, GMT
    },

    # Attempt to order the domains
    'order_domains': {
        'task': 'app.blueprints.api.tasks.order_domains',
        'schedule': 5 * backorder_count  # every second after the previous one completes
    },

    # Delete successfully paid backorders
    # 'delete_backorders': {
    #     'task': 'app.blueprints.api.tasks.delete_backorders',
    #     'schedule': crontab(minute=0, hour=0) # every minute
    # },

    # Retry charges for secured domains that aren't paid.
    # 'retry_charges': {
    #     'task': 'app.blueprints.api.tasks.retry_charges',
    #     'schedule': crontab(minute=0, hour="*/1") # every hour
    #     'schedule': crontab(hour=0, minute=0) # every night at midnight, GMT
    # },
}

'''
Uncomment this code in order to set a worker for each app that uses manual webhoooks.
If uncommenting this code, make sure to comment out the webhooks dict in the above
CELERYBEAT_SCHEDULE dictionary
'''
# webhook_apps = get_webhook_apps()
# for app in webhook_apps:
#     CELERYBEAT_SCHEDULE.update(
#         {
#             app: {
#                 'task': 'app.blueprints.api.apps.' + app + '.webhook.webhook',
#                 'schedule': crontab(minute='*/' + str(CELERY_TASK_FREQUENCY))
#             }
#         })

# SQLAlchemy.
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', None)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_USER = os.environ.get('SQLALCHEMY_USER', None)
SQLALCHEMY_DATABASE = os.environ.get('SQLALCHEMY_DATABASE', None)
SQLALCHEMY_HOST = os.environ.get('SQLALCHEMY_HOST', None)
SQLALCHEMY_PASSWORD = os.environ.get('SQLALCHEMY_PASSWORD', None)

# User.
SEED_ADMIN_EMAIL = os.environ.get('SEED_ADMIN_EMAIL', None)
SEED_ADMIN_PASSWORD = os.environ.get('SEED_ADMIN_PASSWORD', None)
SEED_MEMBER_EMAIL = ''
REMEMBER_COOKIE_DURATION = timedelta(days=90)

# Dynadot
DYNADOT_API_KEY = os.environ.get('DYNADOT_API_KEY', None)

# Godaddy
GODADDY_TEST_API_KEY = os.environ.get('GODADDY_TEST_API_KEY', None)
GODADDY_TEST_SECRET_KEY = os.environ.get('GODADDY_TEST_SECRET_KEY', None)
GODADDY_API_KEY = os.environ.get('GODADDY_API_KEY', None)
GODADDY_SECRET_KEY = os.environ.get('GODADDY_SECRET_KEY', None)
GODADDY_TEST_API_URL = 'https://api.ote-godaddy.com'
GODADDY_API_URL = 'https://api.godaddy.com'

# Namecheap
NAMECHEAP_API_KEY = os.environ.get('NAMECHEAP_API_KEY', None)
NAMECHEAP_SANDBOX_API_KEY = os.environ.get('NAMECHEAP_SANDBOX_API_KEY', None)
NAMECHEAP_USERNAME = os.environ.get('NAMECHEAP_USERNAME', None)
NAMECHEAP_REGISTRATION = {
    'FirstName': os.environ.get('FirstName', None),
    'LastName': os.environ.get('LastName', None),
    'Address1': os.environ.get('Address1', None),
    'City': os.environ.get('City', None),
    'StateProvince': os.environ.get('StateProvince', None),
    'PostalCode': os.environ.get('PostalCode', None),
    'Country': os.environ.get('Country', None),
    'Phone': os.environ.get('Phone', None),
    'EmailAddress': os.environ.get('EmailAddress', None)
}
IP_ADDRESS = os.environ.get('HOME_IP_ADDRESS', None)
WORK_IP_ADDRESS = os.environ.get('WORK_IP_ADDRESS', None)

# Mailgun.
# MAILGUN_LOGIN = os.environ.get('MAILGUN_LOGIN', None)
# MAILGUN_PASSWORD = os.environ.get('MAILGUN_PASSWORD', None)
# MAILGUN_HOST = os.environ.get('MAILGUN_HOST', None)
# MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', None)
# MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', None)

# Turn off debug intercepts
DEBUG_TB_INTERCEPT_REDIRECTS = False
DEBUG_TB_ENABLED = False

# Ngrok
SITE_URL = 'https://getparked.io'

# Webhook
WEBHOOK_URL = 'https://www.getparked.io/webhook'

# Mailerlite
# MAILERLITE_API_KEY = os.environ.get('MAILERLITE_API_KEY', None)

# Billing.
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', None)
STRIPE_TEST_SECRET_KEY = os.environ.get('STRIPE_TEST_SECRET_KEY', None)
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', None)
STRIPE_TEST_PUBLISHABLE_KEY = os.environ.get('STRIPE_TEST_PUBLISHABLE_KEY', None)
STRIPE_API_VERSION = '2018-02-28'
STRIPE_AUTHORIZATION_LINK = os.environ.get('STRIPE_CONNECT_AUTHORIZE_LINK', None)

# Change this to the live key when ready to take payments
STRIPE_KEY = STRIPE_SECRET_KEY

STRIPE_PLANS = {
    '0': {
        'id': 'free',
        'name': 'Free',
        'amount': 0000,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'FREE',
        'metadata': {}
    },
    '1': {
        'id': 'hobby',
        'name': 'Hobby',
        'amount': 700,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'HOBBY',
        'metadata': {}
    },
    '2': {
        'id': 'startup',
        'name': 'Startup',
        'amount': 2000,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'STARTUP',
        'metadata': {
            'recommended': True
        }
    },
    '3': {
        'id': 'professional',
        'name': 'Professional',
        'amount': 5000,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'PROFESSIONAL',
        'metadata': {}
    },
    '4': {
        'id': 'premium',
        'name': 'Premium',
        'amount': 12000,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'PREMIUM',
        'metadata': {}
    },
    '5': {
        'id': 'enterprise',
        'name': 'Enterprise',
        'amount': 25000,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'ENTERPRISE',
        'metadata': {}
    },
    '6': {
        'id': 'developer',
        'name': 'Developer',
        'amount': 1,
        'currency': 'usd',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 0,
        'statement_descriptor': 'DEVELOPER',
        'metadata': {}
    }
}
