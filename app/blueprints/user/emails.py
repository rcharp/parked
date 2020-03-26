__author__ = 'Ricky'
from flask import Flask, render_template
from flask_mail import Mail, Message
from app.app import create_celery_app

celery = create_celery_app()


def send_welcome_email(email):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("You've successfully signed up for NameCatcher.io!",
                  sender="namecatcherio@gmail.com",
                  recipients=[email])

    msg.html = render_template('user/mail/welcome_email.html')

    mail.send(msg)


def send_reservation_email(email, domain, available):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("You've successfully reserved " + domain + "!",
                  sender="namecatcherio@gmail.com",
                  recipients=[email])
    msg.html = render_template('user/mail/reservation_email.html', domain=domain, available=available)

    response = Message("User " + email + " reserved " + domain + ".",
                       recipients=["namecatcherio@gmail.com"],
                       sender="namecatcherio@gmail.com")

    response.body = email + " reserved the following domain:\n\n" + domain + ".\n\nIt's available on " + available + "."

    mail.send(msg)
    mail.send(response)


def send_secured_email(email, domain):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("We successfully secured " + domain + " for you!",
                  sender="namecatcherio@gmail.com",
                  recipients=[email])
    msg.html = render_template('user/mail/secured_domain.html', domain=domain)

    mail.send(msg)


def send_purchase_email(email, domain):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("You've successfully purchased " + domain + "!",
                  sender="namecatcherio@gmail.com",
                  recipients=[email])
    msg.html = render_template('user/mail/purchase_email.html', domain=domain)

    mail.send(msg)


def contact_us_email(email, message):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("[NameCatcher.io Contact] Support request from " + email,
                  recipients=["namecatcherio@gmail.com"],
                  sender="namecatcherio@gmail.com",
                  reply_to=email)
    msg.body = email + " sent you a message:\n\n" + message

    response = Message("Your email to NameCatcher.io has been received.",
                       recipients=[email],
                       sender="namecatcherio@gmail.com")

    response.html = render_template('user/mail/contact_email.html',email=email, message=message)

    mail.send(msg)
    mail.send(response)


def request_email(email, request_to, request_from, message):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("[NameCatcher.io Contact] Support request from " + email,
                  recipients=["namecatcherio@gmail.com"],
                  sender="namecatcherio@gmail.com",
                  reply_to=email)
    msg.body = email + " sent you an integration request:\n\n" + "From: " + request_from + "\n\n" +\
               "To: " + request_to + "\n\n" + \
               "Message: " + message

    response = Message("Your email to NameCatcher.io has been received.",
                       recipients=[email],
                       sender="namecatcherio@gmail.com")

    response.html = render_template('user/mail/request_email.html', email=email, request_from=request_from, request_to=request_to, message=message)

    mail.send(msg)
    mail.send(response)


def send_cancel_email(email):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("Goodbye from NameCatcher.io",
                  sender="namecatcherio@gmail.com",
                  recipients=[email])

    msg.html = render_template('user/mail/cancel_email.html')

    mail.send(msg)
