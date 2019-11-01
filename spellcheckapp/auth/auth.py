import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, make_response
)
from werkzeug.security import check_password_hash, generate_password_hash

from spellcheckapp import db
import sqlite3
from spellcheckapp.auth import forms
from spellcheckapp.auth import models
import re

bp = Blueprint('auth', __name__, template_folder="../templates")

@bp.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.AuthForm()
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
        elif models.User.query.filter_by(username=username).first() is not None:
            error = 'Username is not available.'
            flash(error)
            flash('Registration failure.')

        if error is None:
            if (mfa is None) or (mfa == ''):
                mfa_reg = 0;
            else:
                mfa_reg = 1;
            new_user = models.User(username=username, password=generate_password_hash(password), mfa_registered=mfa_reg)
            db.session.add(new_user)
            if mfa_reg:
                new_mfa = models.MFA(username=username, mfa_number=mfa)
                db.session.add(new_mfa)
            try:
                db.session.commit()
                flash('Registration success.')
            except sqlite3.Error as e:
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
    form = forms.AuthForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        error = None
        user = models.User.query.filter_by(username=username).first()

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
            flash('Login success.')
            return redirect(url_for('auth.login'))

    render = make_response(render_template('auth/login.html', form=form))
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = models.User.query.filter_by(id=user_id).first()


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
