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


class MFAForm(FlaskForm):
    """
    MFA Confirmation Form.

    This form is used to finish MFA setup for a user.
    """

    mfa_confirm = BooleanField(label='Confirm MFA Setup', id='mfa_confirm', default=False, validators=[Optional()])


class LoginForm(FlaskForm):
    """
    Login Form.

    This form is used to login as a user.
    """

    username = StringField(label='Username', id='uname', validators=[DataRequired(), Regexp(regex='^(?=.{5,20}$)[a-zA-Z0-9._]+$', message='Auth failure. Invalid char in username or not between 5 - 20 chars')])  # noqa: E501
    password = PasswordField(label='Password', id='pword', validators=[DataRequired(), Regexp(regex='^(?=.{8,20}$)[a-zA-Z0-9._$%&*#@!]+$', message='Auth failure. Invalid char in password or not between 8 - 20 chars')])  # noqa: E501
    mfa = StringField(label='2FA', id='2fa', validators=[Optional(), Length(6, 6)])


class UpdateAccountForm(FlaskForm):
    """
    Update Account Form.

    This form is used to choose what details to update for a user.
    """

    password = PasswordField(label='Change Password', id='pword', validators=[Optional(), Regexp(regex='^(?=.{8,20}$)[a-zA-Z0-9._$%&*#@!]+$', message='Auth failure. Invalid char in password or not between 8 - 20 chars')])  # noqa: E501
    mfa_enabled = BooleanField(label='MFA Enabled', id='mfa_enabled', validators=[Optional()])


class UserAuthHistoryForm(FlaskForm):
    """
    User Auth History Form.

    This form is used by admins to query for another user's history.
    """

    userid = IntegerField(label="User ID to query", id='userid', validators=[DataRequired()])
