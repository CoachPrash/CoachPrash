from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LinkCodeForm(FlaskForm):
    code = StringField('Parent Link Code', validators=[
        DataRequired(),
        Length(min=8, max=8, message='Link code must be exactly 8 characters.'),
    ])
    submit = SubmitField('Link My Child')
