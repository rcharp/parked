from app.extensions import mail
# from app.blueprints.contact.tasks import deliver_contact_email
from app.blueprints.user.tasks import send_contact_us_email


class TestTasks(object):
    def test_deliver_support_email(self):
        """ Deliver a contact email. """
        form = {
          'email': 'foo@bar.com',
          'message': 'Test message from Parked.'
        }

        with mail.record_messages() as outbox:
            # deliver_contact_email(form.get('email'), form.get('message'))
            send_contact_us_email(form.get('email'), form.get('message'))

            assert len(outbox) == 1
            assert form.get('email') in outbox[0].body
