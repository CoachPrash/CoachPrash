import uuid
from datetime import datetime, timezone
from app.extensions import db


class StudentProgress(db.Model):
    __tablename__ = 'student_progress'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    concept_id = db.Column(db.String(36), db.ForeignKey('concepts.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='not_started')
    mastery_score = db.Column(db.Float, nullable=True)
    last_accessed = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint('student_id', 'concept_id', name='uq_student_concept'),
    )

    def __repr__(self):
        return f'<Progress {self.student_id} - {self.concept_id}>'


class AttemptLog(db.Model):
    __tablename__ = 'attempt_logs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.String(36), db.ForeignKey('problems.id'), nullable=False)
    submitted_answer = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    hints_used = db.Column(db.Integer, nullable=False, default=0)
    time_spent_seconds = db.Column(db.Integer, nullable=True)
    attempted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Attempt {self.id}>'
