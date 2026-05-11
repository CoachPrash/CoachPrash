import uuid
import string
import random
from datetime import datetime, timezone
from app.extensions import db


class AccessCode(db.Model):
    __tablename__ = 'access_codes'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    tier = db.Column(db.String(20), nullable=False, default='premium')
    max_uses = db.Column(db.Integer, nullable=True)
    current_uses = db.Column(db.Integer, nullable=False, default=0)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @staticmethod
    def generate_code(length=8):
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            if not AccessCode.query.filter_by(code=code).first():
                return code

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False
        return True

    def use(self):
        self.current_uses += 1

    def __repr__(self):
        return f'<AccessCode {self.code}>'
