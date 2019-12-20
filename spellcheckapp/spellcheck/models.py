"""Defines Data Models for Spellcheck Module."""
from spellcheckapp import db


class SpellChecks(db.Model):
    """
    SpellChecks Database Model.

    Defines SpellChecks fields.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('users.username'), unique=False, nullable=False)
    submitted_text = db.Column(db.String(501), unique=False, nullable=False)
    misspelled_words = db.Column(db.String(501), unique=False, nullable=True)

    def __repr__(self):
        """Defines string representation of a SpellChecks tuple."""
        return '<User %r Spell_check_id %r>' % (self.username, self.id)
