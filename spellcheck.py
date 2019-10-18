from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from auth import login_required
from db import get_db

bp = Blueprint('spellcheck', __name__)


@bp.route('/')
def index():
    return render_template('spellcheck/index.html')
