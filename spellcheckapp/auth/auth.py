"""
Auth Module for Spellcheckapp.

Contains authentication related views.
"""
import datetime
import functools
import re
import sqlite3

from flask import (
    Blueprint, abort, flash, g, make_response, redirect, render_template, session, url_for
)

from spellcheckapp import db
from spellcheckapp.auth import forms
from spellcheckapp.auth import models

from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('auth', __name__, template_folder="../templates")


def login_required(view):
    """
    Login required wrapper.

    Wraps a view and redirects requests to the view to the login page, unless a user is logged in.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.route('/register', methods=('GET', 'POST'))
def register():
    """
    Register view.

    Defines logic for the register view.
    Performs form validation and handles database calls to create and validate a user.
    Also constructs response with security headers.
    """
    form = forms.AuthForm()
    if g.user is None:
        if form.validate_on_submit():
            # Validate and santize
            username = form.username.data
            password = form.password.data
            mfa = form.mfa.data
            mfa = re.sub(r"\D", "", mfa)
            error = None

            if not username:
                error = 'Username is required.'
                flash(error)
            elif not password:
                error = 'Password is required.'
                flash(error)
            elif models.Users.query.filter_by(username=username).first() is not None:
                error = 'Username is not available.'
                flash(error)
                flash('Registration failure.')

            if error is None:
                if (mfa is None) or (mfa == ''):
                    mfa_reg = 0
                else:
                    mfa_reg = 1
                new_user = models.Users(username=username, password=generate_password_hash(password), mfa_registered=mfa_reg)
                db.session.add(new_user)
                if mfa_reg:
                    new_mfa = models.MFA(username=username, mfa_number=mfa)
                    db.session.add(new_mfa)
                try:
                    db.session.commit()
                    flash('Registration success.')
                except sqlite3.Error:
                    flash('Registration failure.')
                return redirect(url_for('auth.register'))

    render = make_response(render_template('auth/register.html', form=form))
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """
    Login view.

    Defines logic for the login view.
    Performs form validation and handles database calls to validate a user.
    Logs the login time for the session.
    Also constructs response with security headers.
    """
    form = forms.AuthForm()
    if g.user is None:
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            error = None
            user = models.Users.query.filter_by(username=username).first()

            if user is None:
                error = 'Invalid/Incorrect credentials.'
                flash(error)
            elif not check_password_hash(user.password, password):
                error = 'Invalid/Incorrect credentials.'
                flash(error)

            if user is not None:
                if user.mfa_registered:
                    mfa = form.mfa.data
                    mfa = re.sub(r"\D", "", mfa)
                    mfa_stored = models.MFA.query.filter_by(username=username).first()
                    if mfa_stored is None:
                        error = 'Corrupt state, contact site admin.'
                        flash(error)
                    elif not mfa:
                        error = 'Two-factor authentication failure.'
                        flash(error)
                    elif not int(mfa) == int(mfa_stored.mfa_number.strip()):
                        error = 'Two-factor authentication failure.'
                        flash(error)

            if error is None:
                session.clear()
                session['user_id'] = user.id
                new_login = models.AuthLog(userid=user.id, username=username, login_time=datetime.datetime.now())
                db.session.add(new_login)
                db.session.commit()
                session['login_id'] = new_login.id
                flash('Login success.')
                return redirect(url_for('auth.login'))

    render = make_response(render_template('auth/login.html', form=form))
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.route('/login_history', methods=('GET', 'POST'))
@login_required
def login_history():
    """
    Login history view.

    This is an admin only view.
    Defines logic for the login history view.
    Performs form validation and user level validation.
    Also constructs response with security headers.
    """
    if g.user.is_admin:
        form = forms.UserAuthHistoryForm()
        user_auth_history = None
        if form.validate_on_submit():
            userid = form.userid.data
            error = None
            user = models.Users.query.get(userid)

            if user is None:
                error = 'User does not exist.'
                flash(error)

            if user is not None:
                user_auth_history = models.AuthLog.query.filter_by(userid=userid)
                if user_auth_history is None:
                    flash('User has not logged in yet.')

        render = make_response(render_template('auth/login_history.html', form=form, user_auth_history=user_auth_history))
        render.headers.set('Content-Security-Policy', "default-src 'self'")
        render.headers.set('X-Content-Type-Options', 'nosniff')
        render.headers.set('X-Frame-Options', 'SAMEORIGIN')
        render.headers.set('X-XSS-Protection', '1; mode=block')
        return render
    else:
        abort(403)


@bp.before_app_request
def load_logged_in_user():
    """Configures the session information for a logged in user."""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = models.Users.query.filter_by(id=user_id).first()


@bp.route('/logout')
def logout():
    """
    Logout view.

    Defines logic for the logout view.
    Terminates the session and logs the logout time for the session.
    """
    login_id = session.get('login_id')
    login_log = models.AuthLog.query.get(login_id)
    login_log.logout_time = datetime.datetime.now()
    db.session.commit()
    session.clear()
    return redirect(url_for('index'))
