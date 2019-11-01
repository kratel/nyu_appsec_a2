# from flask_sqlalchemy import SQLAlchemy
from spellcheckapp import db

"""
CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  mfa_registered INTEGER NOT NULL
);

CREATE TABLE mfa (
  username TEXT NOT NULL,
  mfa_number TEXT NOT NULL,
  FOREIGN KEY(username) REFERENCES user(username)
);
"""

# db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), unique=False, nullable=False)
    mfa_registered = db.Column(db.Boolean, unique=False, default=False)

    def __repr__(self):
        return '<User %r>' % self.username

class MFA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    mfa_number = db.Column(db.String(20), unique=False, nullable=False)

    def __repr__(self):
        return '<MFA_User %r' % self.username
