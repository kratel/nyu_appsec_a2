# from spellcheckapp.auth.models import db
from spellcheckapp import db

"""
CREATE TABLE mfa (
  username TEXT NOT NULL,
  mfa_number TEXT NOT NULL,
  FOREIGN KEY(username) REFERENCES user(username)
);
"""

class Spell_checks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=False, nullable=False)
    submitted_text = db.Column(db.String(501), unique=False, nullable=False)
    misspelled_words = db.Column(db.String(501), unique=False, nullable=True)

    def __repr__(self):
        return '<User %r Spell_check_id %r>' % (self.username, self.id)
