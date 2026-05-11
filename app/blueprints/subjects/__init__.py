from flask import Blueprint

subjects_bp = Blueprint('subjects', __name__, template_folder='../../templates/subjects')

from app.blueprints.subjects import routes  # noqa: F401, E402
