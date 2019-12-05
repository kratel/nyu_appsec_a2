import os

from flask import Flask, render_template
from spellcheckapp import db
from spellcheckapp.auth import auth, models
from spellcheckapp.spellcheck import spellcheck
from werkzeug.security import generate_password_hash


def page_not_found(e):
  return render_template('404.html'), 404


def create_app(test_config=None):
    # create and configure the app
    app = Flask('__name__', instance_relative_config=True, static_url_path='/static', static_folder='spellcheckapp/static',)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'spellchecker.sqlite'),
        SPELLCHECK='./a.out',
        WORDLIST='wordlist.txt',
        SQLALCHEMY_DATABASE_URI='sqlite:///' +  os.path.join(app.instance_path, 'spellchecker.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_HTTPONLY=True,
    )
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Associate db with app
    db.init_app(app)
    # Add the models so that create and drop all know which tables to manage
    from spellcheckapp.auth.models import User, MFA
    from spellcheckapp.spellcheck.models import Spell_checks

    with app.app_context():
        db.drop_all()
        db.create_all()

        try:
            # Create default admin
            d_admin = models.User(username=app.config['ADMIN_USERNAME'], password=generate_password_hash(app.config['ADMIN_PASSWORD']), mfa_registered=True, is_admin=True)
            d_admin_mfa = models.MFA(username=app.config['ADMIN_USERNAME'], mfa_number=app.config['ADMIN_MFA'])
            db.session.add(d_admin)
            db.session.add(d_admin_mfa)
            db.session.commit()
        except KeyError as e:
            print("Admin credentials must be defined in config")


    app.register_blueprint(auth.bp)

    app.register_blueprint(spellcheck.bp)
    app.add_url_rule('/', endpoint='index')
    app.register_error_handler(404, page_not_found)

    return app

if __name__ == '__main__':
    app = create_app()
