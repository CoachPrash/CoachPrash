import uuid
from datetime import datetime, timezone
from app.extensions import db


class Theme(db.Model):
    __tablename__ = 'themes'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Seed colors (admin enters these 4)
    color_primary = db.Column(db.String(7), nullable=False)
    color_secondary = db.Column(db.String(7), nullable=False)
    color_accent = db.Column(db.String(7), nullable=False)
    color_bg = db.Column(db.String(7), nullable=False)

    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Theme {self.name}>'
