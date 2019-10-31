import os

from flask import Flask
from spellcheckapp import db
from spellcheckapp.auth import auth
from spellcheckapp.spellcheck import spellcheck


def create_app(test_config=None):
    # create and configure the app
    app = Flask('__name__', instance_relative_config=True, static_url_path='/static', static_folder='spellcheckapp/static',)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'spellchecker.sqlite'),
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

    with app.app_context():
        db.init_db()
    db.init_app(app)

    app.register_blueprint(auth.bp)

    app.register_blueprint(spellcheck.bp)
    app.add_url_rule('/', endpoint='index')

    return app

if __name__ == '__main__':
    app = create_app()
