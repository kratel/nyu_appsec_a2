from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Regexp, Optional, Length


class SpellCheckForm(FlaskForm):
	inputtext = TextAreaField(label='Input Text to Spell Check', id='inputtext', validators=[DataRequired(), Length(max=500, message='Exceeded max text length: 500')])
