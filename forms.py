from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Regexp, Optional

class AuthForm(FlaskForm):
	username = StringField(label='Username', id='uname', validators=[DataRequired(), Regexp(regex='^(?=.{8,20}$)[a-zA-Z0-9.]+$', message='Registration failure. Invalid char in username or not between 8 - 20 chars')])
	password = PasswordField(label='Password', id='pword', validators=[DataRequired(), Regexp(regex='^(?=.{8,20}$)[a-zA-Z0-9._$%&*#@!]+$', message='Registration failure. Invalid char in password or not between 8 - 20 chars')])
	mfa = IntegerField(label='2FA', id='2fa', validators=[Optional()])


class SpellCheckForm(FlaskForm):
	inputtext = TextAreaField(label='Input Text to Spell Check', id='inputtext', validators=[DataRequired()])
