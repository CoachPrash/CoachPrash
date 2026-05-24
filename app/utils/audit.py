import json
import logging
from flask import request
from flask_login import current_user
from app.extensions import db
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def log_audit(action, entity_type, entity_id=None, details=None):
    """Record an admin action in the audit log."""
    user_id = current_user.id if current_user and current_user.is_authenticated else None
    detail_str = json.dumps(details) if isinstance(details, dict) else details
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=detail_str,
        ip_address=request.remote_addr if request else None,
    )
    db.session.add(entry)
    logger.info('AUDIT: %s %s %s by user=%s', action, entity_type, entity_id, user_id)
