from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Regexp, Optional, Length


class SpellCheckForm(FlaskForm):
	inputtext = TextAreaField(label='Input Text to Spell Check', id='inputtext', validators=[DataRequired(), Length(max=500, message='Exceeded max text length: 500')])


class UserHistoryForm(FlaskForm):
	userquery = StringField(label="Username to query", id='userquery', validators=[DataRequired(), Regexp(regex='^(?=.{5,20}$)[a-zA-Z0-9._]+$', message='Invalid char in username or not between 5 - 20 chars')])
