from flask import Blueprint

volunteers_bp = Blueprint('volunteers', __name__)

from . import routes
