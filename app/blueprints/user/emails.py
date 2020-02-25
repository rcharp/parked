__author__ = 'Ricky'
from flask import Flask, render_template
from flask_mail import Mail, Message
from app.app import create_celery_app

celery = create_celery_app()


def send_welcome_email(email):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("You've successfully signed up for Getparked.io!",
                  sender="getparkedio@gmail.com",
                  recipients=[email])

    msg.html = render_template('user/mail/welcome_email.html')

    mail.send(msg)

    print("Email was sent successfully")


def send_plan_signup_email(email, plan):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("You've subscribed to a plan with Getparked.io!",
                  sender="getparkedio@gmail.com",
                  recipients=[email])
    if plan == 'hobby':
        plan = 'Hobby'
        amount = 7
    elif plan == 'startup':
        plan = 'Startup'
        amount = 20
    elif plan == 'professional':
        plan = 'Professional'
        amount = 50
    else:
        amount = 0
    msg.html = render_template('user/mail/plan_signup_email.html', plan=plan, amount=amount)

    mail.send(msg)


def send_plan_change_email(email, plan):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("Your plan with Getparked.io has been changed.",
                  sender="getparkedio@gmail.com",
                  recipients=[email])
    if plan['id'] == 'hobby':
        plan = 'Hobby'
        amount = 7
    elif plan['id'] == 'startup':
        plan = 'Startup'
        amount = 20
    elif plan['id'] == 'professional':
        plan = 'Professional'
        amount = 50
    else:
        amount = 0
    msg.html = render_template('user/mail/plan_change_email.html', plan=plan, amount=amount)

    mail.send(msg)


def send_three_day_expiration_email(email):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("Your free trial with Getparked.io expires in 3 days.",
                  sender="getparkedio@gmail.com",
                  recipients=[email])
    msg.html = render_template('user/mail/three_day_expiration_email.html')

    mail.send(msg)


def send_trial_expired_email(email):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("Your free trial with Getparked.io has expired.",
                  sender="getparkedio@gmail.com",
                  recipients=[email])
    msg.html = render_template('user/mail/trial_expired_email.html')

    mail.send(msg)


def contact_us_email(email, message):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("[Getparked.io Contact] Support request from " + email,
                  recipients=["getparkedio@gmail.com"],
                  sender="getparkedio@gmail.com",
                  reply_to=email)
    msg.body = email + " sent you a message:\n\n" + message

    response = Message("Your email to Getparked.io has been received.",
                       recipients=[email],
                       sender="getparkedio@gmail.com")

    response.html = render_template('user/mail/contact_email.html',email=email, message=message)

    print(msg)

    mail.send(msg)
    mail.send(response)

    print("Email sent")


def request_email(email, request_to, request_from, message):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("[Getparked.io Contact] Support request from " + email,
                  recipients=["getparkedio@gmail.com"],
                  sender="getparkedio@gmail.com",
                  reply_to=email)
    msg.body = email + " sent you an integration request:\n\n" + "From: " + request_from + "\n\n" +\
               "To: " + request_to + "\n\n" + \
               "Message: " + message

    response = Message("Your email to Getparked.io has been received.",
                       recipients=[email],
                       sender="getparkedio@gmail.com")

    response.html = render_template('user/mail/request_email.html', email=email, request_from=request_from, request_to=request_to, message=message)

    mail.send(msg)
    mail.send(response)


def send_cancel_email(email):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("Goodbye from Getparked.io",
                  sender="getparkedio@gmail.com",
                  recipients=[email])

    msg.html = render_template('user/mail/cancel_email.html')

    mail.send(msg)


def send_failed_log_email(email, integration_id, failure_time):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("Getparked.io: Integration #" + str(integration_id) + " for " + email + " failed.",
                  sender="getparkedio@gmail.com",
                  recipients=['logs@Getparked.io.com'])

    from app.blueprints.api.models.user_integrations import UserIntegration

    integration = UserIntegration.query.filter(UserIntegration.id == integration_id).scalar()

    from app.blueprints.page.date import get_dt_string, get_datetime_from_string
    failure_time = get_dt_string(get_datetime_from_string(failure_time)) + ' (UTC)'

    msg.html = render_template('user/mail/send_failed_log_email.html', integration=integration, email=email, failure_time=failure_time)

    mail.send(msg)