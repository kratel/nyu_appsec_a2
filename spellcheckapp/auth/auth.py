"""
Auth Module for Spellcheckapp.

Contains authentication related views.
All responses are constructed with security headers.
"""
import datetime
import functools
import sqlite3

from flask import (
    Blueprint, abort, flash, g, make_response, redirect, render_template, session, url_for
)

import pyqrcode

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
    """
    form = forms.RegisterForm()
    if g.user is None:
        if form.validate_on_submit():
            # Validate and santize
            username = form.username.data
            password = form.password.data
            error = None

            if models.Users.query.filter_by(username=username).first() is not None:
                error = 'Username is not available.'
                flash(error)
                flash('Registration failure.')

            if error is None:
                new_user = models.Users(username=username, password=generate_password_hash(password), mfa_registered=False)
                db.session.add(new_user)
                try:
                    db.session.commit()
                    flash('User Registration success.')
                except sqlite3.Error:
                    flash('User Registration failure.')
                return redirect(url_for('auth.register'))

    render = make_response(render_template('auth/register.html', form=form))
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.route('/account', methods=('GET', 'POST'))
@login_required
def account():
    """
    Account Page View.

    Displays form to update user account details..
    """
    mfa_status = g.user.mfa_registered
    form = forms.UpdateAccountForm(mfa_enabled=mfa_status)
    if form.validate_on_submit():
        password = form.password.data
        mfa_enabled = form.mfa_enabled.data
        user = models.Users.query.filter_by(username=g.user.username).first()

        if password:
            user.password = generate_password_hash(password)
            db.session.commit()
            flash('Password has been updated.')

        if mfa_enabled != user.mfa_registered:
            cur_mfa = models.MFA.query.filter_by(username=g.user.username).first()
            if cur_mfa is not None:
                db.session.delete(cur_mfa)
                db.session.commit()
            if mfa_enabled:
                new_mfa = models.MFA(username=g.user.username)
                db.session.add(new_mfa)
                db.session.commit()
                return redirect(url_for('auth.mfa_setup'))
            else:
                user.mfa_registered = False
                db.session.commit()
                flash('MFA has been disabled.')
    render = make_response(render_template('auth/account.html', form=form))
    render.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
    render.headers.set('Pragma', 'no-cache')
    render.headers.set('Expires', '0')
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.route('/multifactor', methods=('GET', 'POST'))
@login_required
def mfa_setup():
    """
    Multi Factor Setup View.

    Displays QR Code for MFA token setup.
    """
    form = forms.MFAForm()
    if g.user.mfa_registered:
        return redirect(url_for('auth.account'))
    if form.validate_on_submit():
        mfa_confirm = form.mfa_confirm.data
        if mfa_confirm:
            user = models.Users.query.filter_by(username=g.user.username).first()
            user.mfa_registered = True
            db.session.commit()
            flash('MFA Setup success.')
        else:
            flash('MFA was not enabled.')
        return redirect(url_for('auth.account'))
    render = make_response(render_template('auth/mfa_setup.html', form=form))
    render.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
    render.headers.set('Pragma', 'no-cache')
    render.headers.set('Expires', '0')
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.route('/qrcode')
@login_required
def qrcode():
    """
    QR Code Generator.

    Generates QR Code for MFA.
    """
    mfa_candidate = models.MFA.query.filter_by(username=g.user.username).first()
    if mfa_candidate is None:
        abort(404)
    if g.user.mfa_registered:
        abort(404)

    # render qrcode
    url = pyqrcode.create(mfa_candidate.get_totp_uri())
    from io import BytesIO
    stream = BytesIO()
    url.svg(stream, scale=5)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Content-Security-Policy': "default-src 'self'",
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block'}


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """
    Login view.

    Defines logic for the login view.
    Performs form validation and handles database calls to validate a user.
    Logs the login time for the session.
    """
    form = forms.LoginForm()
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
                    mfa_stored = models.MFA.query.filter_by(username=username).first()
                    if mfa_stored is None:
                        error = 'Corrupt state, contact site admin.'
                        flash(error)
                    elif not mfa_stored.verify_totp(mfa):
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
    An admin can use the form to query for other user login histories using a user ID.
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
