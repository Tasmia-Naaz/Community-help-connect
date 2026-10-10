from flask import Blueprint

help_requests_bp = Blueprint('help_requests', __name__)

from . import routes
