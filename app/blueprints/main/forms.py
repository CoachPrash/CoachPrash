from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length


class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    subject = SelectField(
        'Subject',
        choices=[
            ('general', 'General Inquiry'),
            ('tutoring', 'Tutoring Information'),
            ('pricing', 'Pricing & Plans'),
            ('technical', 'Technical Support'),
            ('other', 'Other'),
        ],
        validators=[DataRequired()],
    )
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=5000)])
