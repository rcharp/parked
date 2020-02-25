from lib.flask_mailplus import send_template_message
from app.app import create_celery_app
from app.blueprints.user.emails import contact_us_email

celery = create_celery_app()


# @celery.task()
def deliver_contact_email(email, message):
    # """
    # Send a contact e-mail.
    #
    # :param email: E-mail address of the visitor
    # :type user_id: str
    # :param message: E-mail message
    # :type user_id: str
    # :return: None
    # """
    # ctx = {'email': email, 'message': message}
    #
    # send_template_message(subject='[Domain] Contact',
    #                       sender=email,
    #                       recipients=[celery.conf.get('MAIL_USERNAME')],
    #                       reply_to=email,
    #                       template='contact/mail/index', ctx=ctx)
    #
    # return None
    contact_us_email(email, message)
