"""Defines Data Models for Auth Module."""
from spellcheckapp import db


class Users(db.Model):
    """
    Users Database Model.

    Defines Users fields.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), unique=False, nullable=False)
    mfa_registered = db.Column(db.Boolean, unique=False, default=False)
    is_admin = db.Column(db.Boolean, unique=False, default=False)

    def __repr__(self):
        """Defines string representation of a Users tuple."""
        return '<User %r>' % self.username


class MFA(db.Model):
    """
    MFA Database Model.

    Defines MFA fields with a foreign key constraint dependent on the User model.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('users.username'), nullable=False)
    mfa_number = db.Column(db.String(20), unique=False, nullable=False)

    def __repr__(self):
        """Defines string representation of a MFA tuple."""
        return '<MFA_User %r' % self.username


class AuthLog(db.Model):
    """
    AuthLog Database Model.

    Defines AuthLog fields with a foreign key constraint dependent on the User model.
    """

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'))
    username = db.Column(db.String(20), db.ForeignKey('users.username'), nullable=False)
    login_time = db.Column(db.DateTime(), nullable=False)
    logout_time = db.Column(db.DateTime(), nullable=True)

    def __repr__(self):
        """Defines string representation of an AuthLog tuple."""
        return '<AuthLog %r' % self.id
