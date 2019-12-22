"""
SpellCheck Module for Spellcheckapp.

Contains spell check related views.
All responses are constructed with security headers.
"""
import subprocess
import tempfile
from shlex import quote

from flask import (
    Blueprint, current_app, flash, g, make_response, render_template
)

from spellcheckapp import db
from spellcheckapp.auth import models as authmodels
from spellcheckapp.auth.auth import login_required
from spellcheckapp.spellcheck import forms, models

from werkzeug.exceptions import abort


bp = Blueprint('spellcheck', __name__, template_folder="spellcheckapp/templates")


@bp.route('/')
def index():
    """
    Index View.

    Landing page for the app at root of the site.
    """
    render = make_response(render_template('spellcheck/index.html'))
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.route('/spell_check', methods=('GET', 'POST'))
@login_required
def spell_check():
    """
    Spell Check View.

    Must be logged in to access this view, otherwise redirected to login page.
    Text is submitted here to be spell checked.
    Text submissions and results are stored as query history for the logged in user.
    """
    form = forms.SpellCheckForm()
    results = {}
    if form.validate_on_submit():
        inputtext = quote(form.inputtext.data)
        inputtext += " "
        error = None

        if not inputtext:
            error = "Invalid input"
            flash(error)

        inputtext = bytes(inputtext, 'utf-8')
        results["textout"] = inputtext.decode()

        new_spell_check = None
        if error is None:
            result = None
            with tempfile.NamedTemporaryFile() as inputfile:
                # inputfile = tempfile.NamedTemporaryFile()
                inputfile.write(inputtext)
                inputfile.flush()
                with tempfile.TemporaryFile() as tempf:
                    proc = subprocess.Popen([current_app.config['SPELLCHECK'], inputfile.name, current_app.config['WORDLIST']], stdout=tempf)
                    proc.wait()
                    tempf.seek(0)
                    result = tempf.read()
            result = result.decode().split("\n")
            result = list(filter(None, result))
            if result:
                results["misspelled"] = ", ".join(result)
                new_spell_check = models.SpellChecks(username=g.user.username, submitted_text=results["textout"], misspelled_words=results["misspelled"])
            else:
                results["no_misspelled"] = "No misspelled words were found."
                new_spell_check = models.SpellChecks(username=g.user.username, submitted_text=results["textout"], misspelled_words=results["no_misspelled"])

        if new_spell_check is not None:
            db.session.add(new_spell_check)
            db.session.commit()

    render = make_response(render_template('spellcheck/spell_check.html', form=form, results=results))
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.route('/history', methods=('GET', 'POST'))
@login_required
def history():
    """
    History View.

    Must be logged in to access this view, otherwise redirected to login page.
    This page will list links to queries that the user has submitted.
    Will also show total number of queries submitted so far.

    If an admin user visits this page, there will be a form available.
    Admins can lookup another user's history by submitting a username.
    Performs form validation and user level validation.
    """
    render = None
    form = forms.UserHistoryForm()
    username = g.user.username
    queryhistory = models.SpellChecks.query.filter_by(username=username)
    numqueries = queryhistory.count()

    if g.user.is_admin:
        if form.validate_on_submit():
            quser = form.userquery.data
            error = None

            if not quser:
                error = "Invalid input"
                flash(error)
            elif authmodels.Users.query.filter_by(username=quser).first() is None:
                error = "No user with this username found"
                flash(error)

            if error is None:
                username = quser
                queryhistory = models.SpellChecks.query.filter_by(username=username)
                numqueries = queryhistory.count()

    if g.user.is_admin:
        render = make_response(render_template('spellcheck/history.html', form=form, numqueries=numqueries, queryhistory=queryhistory, username=username))
    else:
        render = make_response(render_template('spellcheck/history.html', numqueries=numqueries, queryhistory=queryhistory, username=username))
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.route('/history/query<int:queryid>', methods=['GET'])
@login_required
def query(queryid):
    """
    Dynamic Query View.

    Must be logged in to access this view, otherwise redirected to login page.
    A unique view is generated based off a query ID.
    A page is only returned if the query ID is associated with a logged in user.
    Otherwise a logged in user will be redirected to a 404 error page.
    """
    query = models.SpellChecks.query.get(queryid)
    if query is not None and ((g.user.is_admin) or (g.user.username == query.username)):
        query
        render = make_response(render_template('spellcheck/history_s_query.html', query=query))
        render.headers.set('Content-Security-Policy', "default-src 'self'")
        render.headers.set('X-Content-Type-Options', 'nosniff')
        render.headers.set('X-Frame-Options', 'SAMEORIGIN')
        render.headers.set('X-XSS-Protection', '1; mode=block')
        return render
    else:
        abort(404)
