import uuid
import string
import random
from datetime import datetime, timezone, timedelta
from app.extensions import db


class ParentStudentLink(db.Model):
    __tablename__ = 'parent_student_links'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    parent = db.relationship('User', foreign_keys=[parent_id], backref='linked_students')
    student = db.relationship('User', foreign_keys=[student_id], backref='linked_parents')

    __table_args__ = (
        db.UniqueConstraint('parent_id', 'student_id', name='uq_parent_student'),
    )

    def __repr__(self):
        return f'<ParentStudentLink {self.parent_id} -> {self.student_id}>'


class ParentLinkCode(db.Model):
    __tablename__ = 'parent_link_codes'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)

    student = db.relationship('User', foreign_keys=[student_id])
    used_by_user = db.relationship('User', foreign_keys=[used_by])

    def __repr__(self):
        return f'<ParentLinkCode {self.code} for student {self.student_id}>'

    @staticmethod
    def generate_code(length=8):
        """Generate a unique alphanumeric code."""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            if not ParentLinkCode.query.filter_by(code=code).first():
                return code

    @staticmethod
    def create_for_student(student_id, days_valid=7):
        """Create a new link code for a student with expiry."""
        code = ParentLinkCode(
            code=ParentLinkCode.generate_code(),
            student_id=student_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=days_valid),
        )
        db.session.add(code)
        db.session.commit()
        return code

    def is_valid(self):
        """Check if code is unused and not expired."""
        if self.is_used:
            return False
        if self.expires_at:
            now = datetime.now(timezone.utc)
            expires = self.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if now > expires:
                return False
        return True
