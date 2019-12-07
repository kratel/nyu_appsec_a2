from spellcheckapp import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), unique=False, nullable=False)
    mfa_registered = db.Column(db.Boolean, unique=False, default=False)
    is_admin = db.Column(db.Boolean, unique=False, default=False)

    def __repr__(self):
        return '<User %r>' % self.username


class MFA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
    mfa_number = db.Column(db.String(20), unique=False, nullable=False)

    def __repr__(self):
        return '<MFA_User %r' % self.username


class AuthLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
    login_time = db.Column(db.DateTime(), nullable=False)
    logout_time = db.Column(db.DateTime(), nullable=True)
    def __repr__(self):
        return '<AuthLog %r' % self.id
