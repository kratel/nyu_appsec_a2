from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort

from spellcheckapp.auth import login_required
from spellcheckapp.db import get_db
from spellcheckapp import forms
from shlex import quote
import subprocess
import tempfile

bp = Blueprint('spellcheck', __name__, template_folder="templates")


@bp.route('/')
def index():
	return render_template('spellcheck/index.html')


@bp.route('/spell_check', methods=('GET', 'POST'))
@login_required
def spell_check():
	form = forms.SpellCheckForm()
	results = {}
	if form.validate_on_submit():
		inputtext = quote(form.inputtext.data)
		inputtext += "\r\n"
		error = None

		if not inputtext:
			error = "Invalid input"
			flash(error)

		inputtext = bytes(inputtext, 'utf-8')
		results["textout"] = inputtext.decode()

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
			else:
				results["no_misspelled"] = "No misspelled words were found."

	return render_template('spellcheck/spell_check.html', form=form, results=results)
