"""Defines Data Models for Spellcheck Module."""
from spellcheckapp import db


class Spell_checks(db.Model):
    """
    Spell_checks Database Model.

    Defines Spell_checks fields.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('user.username'), unique=False, nullable=False)
    submitted_text = db.Column(db.String(501), unique=False, nullable=False)
    misspelled_words = db.Column(db.String(501), unique=False, nullable=True)

    def __repr__(self):
        """Defines string representation of a Spell_checks tuple."""
        return '<User %r Spell_check_id %r>' % (self.username, self.id)
