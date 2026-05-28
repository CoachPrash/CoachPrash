from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False)  # e.g. 'create', 'update', 'delete'
    entity_type = db.Column(db.String(50), nullable=False)  # e.g. 'Subject', 'User'
    entity_id = db.Column(db.String(36), nullable=True)
    details = db.Column(db.Text, nullable=True)  # JSON string with change details
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type} by {self.user_id}>'
