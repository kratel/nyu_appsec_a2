from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, make_response
)
from werkzeug.exceptions import abort

from spellcheckapp import db
from spellcheckapp.auth.auth import login_required
from spellcheckapp.auth import models as authmodels
from spellcheckapp.spellcheck import forms, models
from shlex import quote
import subprocess
import tempfile

bp = Blueprint('spellcheck', __name__, template_folder="spellcheckapp/templates")


@bp.route('/')
def index():
    render = make_response(render_template('spellcheck/index.html'))
    render.headers.set('Content-Security-Policy', "default-src 'self'")
    render.headers.set('X-Content-Type-Options', 'nosniff')
    render.headers.set('X-Frame-Options', 'SAMEORIGIN')
    render.headers.set('X-XSS-Protection', '1; mode=block')
    return render


@bp.route('/spell_check', methods=('GET', 'POST'))
@login_required
def spell_check():
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
                    proc = subprocess.Popen([current_app.config['SPELLCHECK'], current_app.config['WORDLIST'], inputfile.name], stdout=tempf)
                    proc.wait()
                    tempf.seek(0)
                    result = tempf.read()
            result = result.decode().split("\n")
            result = list(filter(None, result))
            if result:
                results["misspelled"] = ", ".join(result)
                new_spell_check = models.Spell_checks(username=g.user.username, submitted_text=results["textout"], misspelled_words=results["misspelled"])
            else:
                results["no_misspelled"] = "No misspelled words were found."
                new_spell_check = models.Spell_checks(username=g.user.username, submitted_text=results["textout"], misspelled_words=results["no_misspelled"])

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
    render = None
    form = forms.UserHistoryForm()
    results = {}
    username = g.user.username
    queryhistory = models.Spell_checks.query.filter_by(username=username)
    numqueries = queryhistory.count()

    if g.user.is_admin:
        if form.validate_on_submit():
            quser = form.userquery.data
            error = None

            if not quser:
                error = "Invalid input"
                flash(error)
            elif authmodels.User.query.filter_by(username=quser).first() is None:
                error = "No user with this username found"
                flash(error)

            if error is None:
                username = quser
                queryhistory = models.Spell_checks.query.filter_by(username=username)
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
    query = models.Spell_checks.query.get(queryid)
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
