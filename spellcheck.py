from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from auth import login_required
from db import get_db
import forms

bp = Blueprint('spellcheck', __name__)


@bp.route('/')
def index():
	return render_template('spellcheck/index.html')


@bp.route('/spell_check', methods=('GET', 'POST'))
@login_required
def spell_check():
	form = forms.SpellCheckForm()
	if form.validate_on_submit():
		inputtext = form.inputtext.data
		error = None

		if error is None:
			return redirect(url_for('spellcheck.spell_check'))

	return render_template('spellcheck/spell_check.html', form=form)
