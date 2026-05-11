from flask import Blueprint

study_bp = Blueprint('study', __name__, template_folder='../../templates/study')

from app.blueprints.study import routes  # noqa: F401, E402
