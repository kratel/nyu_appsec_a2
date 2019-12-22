"""Defines forms for the SpellCheck module."""
from flask_wtf import FlaskForm

from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp


class SpellCheckForm(FlaskForm):
    """
    Spell Check Submission Form.

    This form is used to submit text for spell checking.
    """

    inputtext = TextAreaField(label='Input Text to Spell Check', id='inputtext', validators=[DataRequired(), Length(max=500, message='Exceeded max text length: 500')])  # noqa: E501


class UserHistoryForm(FlaskForm):
    """
    User Spell Check History Form.

    This form is used for an admin to query other user's submission histories.
    """

    userquery = StringField(label="Username to query", id='userquery', validators=[DataRequired(), Regexp(regex='^(?=.{5,20}$)[a-zA-Z0-9._]+$', message='Invalid char in username or not between 5 - 20 chars')])  # noqa: E501
