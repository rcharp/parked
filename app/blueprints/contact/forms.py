from flask_wtf import Form
from wtforms import TextAreaField
from wtforms_components import EmailField
from wtforms.validators import DataRequired, Length


class ContactForm(Form):
    email = EmailField("What's your email address?",
                       [DataRequired(), Length(3, 254)])
    message = TextAreaField("Questions? Concerns? Just want to tell us we're awesome? Let us know below!",
                            [DataRequired(), Length(1, 8192)])
