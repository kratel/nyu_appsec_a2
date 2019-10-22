import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

import sqlite3
import forms

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.AuthForm()
    if form.validate_on_submit():
    	# Validate and santize
        username = form.username.data
        password = form.password.data
        mfa = form.mfa.data
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
            flash(error)
        elif not password:
            error = 'Password is required.'
            flash(error)
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

    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.AuthForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Invalid credentials.'
            flash(error)
        elif not check_password_hash(user['password'], password):
            error = 'Invalid credentials.'
            flash(error)

        if user is not None:
            if user['mfa_registered']:
                mfa = form.mfa.data
                mfa_stored = db.execute(
                    'SELECT * FROM mfa WHERE username = ?', (user['username'],)
                ).fetchone()
                if mfa_stored is None:
                    error = 'Corrupt state, contact site admin.'
                    flash(error)
                elif not int(mfa) == int(mfa_stored['mfa_number'].strip()):
                    error = 'Two-factor authentication failure.'
                    flash(error)

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            flash('Login success.')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html', form=form)


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
