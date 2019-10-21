import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

import sqlite3

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
    	# Validate and santize
        username = request.form['username']
        password = request.form['password']
        mfa = request.form['2fa']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'Username is not available.'
            flash(error)
            flash('Registration failure.')

        if error is None:
            if (mfa is None) or (mfa == ''):
                mfa_reg = 0;
            else:
                mfa_reg = 1;
            db.execute(
                'INSERT INTO user (username, password, mfa_registered) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), mfa_reg)
            )
            if mfa_reg:
                db.execute(
                    'INSERT INTO mfa (username, mfa_number) VALUES (?, ?)',
                    (username, mfa)
                )
            try:
                db.commit()
                flash('Registration success.')
            except sqlite3.Error as e:
                flash('Registration failure.')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Invalid credentials.'
        elif not check_password_hash(user['password'], password):
            error = 'Invalid credentials.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
