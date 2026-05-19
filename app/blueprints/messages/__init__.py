from flask import Blueprint

messages_bp = Blueprint('messages', __name__, template_folder='../../templates/messages')

from app.blueprints.messages import routes  # noqa: F401, E402
