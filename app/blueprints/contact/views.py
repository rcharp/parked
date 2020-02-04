from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    url_for,
    render_template)
from flask_login import current_user

from app.blueprints.contact.forms import ContactForm

contact = Blueprint('contact', __name__, template_folder='templates')


@contact.route('/contact2', methods=['GET', 'POST'])
def index():
    # Pre-populate the email field if the user is signed in.
    form = ContactForm(obj=current_user)

    if form.validate_on_submit():
        # This prevents circular imports.
        # from app.blueprints.contact.tasks import deliver_contact_email
        from app.blueprints.user.tasks import send_contact_us_email

        # deliver_contact_email(request.form.get('email'), request.form.get('message'))
        send_contact_us_email.delay(request.form.get('email'), request.form.get('message'))

        flash('Thanks for your email! You can expect a response shortly.', 'success')
        return redirect(url_for('contact.index'))

    return render_template('contact/index.html', form=form)
