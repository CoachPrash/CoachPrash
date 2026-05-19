from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length


class ComposeForm(FlaskForm):
    recipient_id = SelectField('To', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField('Message', validators=[DataRequired()])


class ReplyForm(FlaskForm):
    body = TextAreaField('Reply', validators=[DataRequired()])
