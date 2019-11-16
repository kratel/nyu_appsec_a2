from spellcheckapp import db
from spellcheckapp.auth.models import User

class Spell_checks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('user.username'), unique=False, nullable=False)
    submitted_text = db.Column(db.String(501), unique=False, nullable=False)
    misspelled_words = db.Column(db.String(501), unique=False, nullable=True)

    def __repr__(self):
        return '<User %r Spell_check_id %r>' % (self.username, self.id)
