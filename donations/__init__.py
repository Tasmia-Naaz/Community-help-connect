from flask import Blueprint

donations_bp = Blueprint('donations', __name__)

from . import routes
