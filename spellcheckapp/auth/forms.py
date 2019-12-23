"""Defines forms for the Auth module."""
from flask_wtf import FlaskForm

from wtforms import BooleanField, IntegerField, PasswordField, StringField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class RegisterForm(FlaskForm):
    """
    Register Form.

    This form is used to register a user.
    """

    username = StringField(label='Username', id='uname', validators=[DataRequired(), Regexp(regex='^(?=.{5,20}$)[a-zA-Z0-9._]+$', message='Auth failure. Invalid char in username or not between 5 - 20 chars')])  # noqa: E501
    password = PasswordField(label='Password', id='pword', validators=[DataRequired(), Regexp(regex='^(?=.{8,20}$)[a-zA-Z0-9._$%&*#@!]+$', message='Auth failure. Invalid char in password or not between 8 - 20 chars')])  # noqa: E501
    mfa = BooleanField(label='2FA', id='2fa', default=False, validators=[Optional()])


class LoginForm(FlaskForm):
    """
    Login Form.

    This form is used to login as a user.
    """

    username = StringField(label='Username', id='uname', validators=[DataRequired(), Regexp(regex='^(?=.{5,20}$)[a-zA-Z0-9._]+$', message='Auth failure. Invalid char in username or not between 5 - 20 chars')])  # noqa: E501
    password = PasswordField(label='Password', id='pword', validators=[DataRequired(), Regexp(regex='^(?=.{8,20}$)[a-zA-Z0-9._$%&*#@!]+$', message='Auth failure. Invalid char in password or not between 8 - 20 chars')])  # noqa: E501
    mfa = StringField(label='2FA', id='2fa', validators=[Optional(), Length(max=20)])


class UserAuthHistoryForm(FlaskForm):
    """
    User Auth History Form.

    This form is used by admins to query for another user's history.
    """

    userid = IntegerField(label="User ID to query", id='userid', validators=[DataRequired()])
