"""Inits spellcheckapp, creates app-wide reference for SQLAlchemy object."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
