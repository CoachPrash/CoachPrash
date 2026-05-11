from flask import Blueprint

admin_bp = Blueprint('admin_panel', __name__, template_folder='../../templates/admin')

from app.blueprints.admin_panel import routes  # noqa: F401, E402
