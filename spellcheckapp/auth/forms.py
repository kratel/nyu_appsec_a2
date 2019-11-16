from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Regexp, Optional, Length


class AuthForm(FlaskForm):
	username = StringField(label='Username', id='uname', validators=[DataRequired(), Regexp(regex='^(?=.{5,20}$)[a-zA-Z0-9._]+$', message='Auth failure. Invalid char in username or not between 5 - 20 chars')])
	password = PasswordField(label='Password', id='pword', validators=[DataRequired(), Regexp(regex='^(?=.{8,20}$)[a-zA-Z0-9._$%&*#@!]+$', message='Auth failure. Invalid char in password or not between 8 - 20 chars')])
	mfa = StringField(label='2FA', id='2fa', validators=[Optional(), Length(max=20)])


class UserAuthHistoryForm(FlaskForm):
	userid = IntegerField(label="User ID to query", id='userid', validators=[DataRequired()])
