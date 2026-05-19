import uuid
from datetime import datetime, timezone
from app.extensions import db


class StudentReport(db.Model):
    __tablename__ = 'student_reports'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    report_month = db.Column(db.Integer, nullable=False)
    report_year = db.Column(db.Integer, nullable=False)
    generated_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    summary_json = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    student = db.relationship('User', foreign_keys=[student_id], backref='reports')
    generator = db.relationship('User', foreign_keys=[generated_by])

    __table_args__ = (
        db.UniqueConstraint('student_id', 'report_month', 'report_year', name='uq_student_report_period'),
    )

    @property
    def period_label(self):
        """Human-readable period like 'May 2026'."""
        import calendar
        return f'{calendar.month_name[self.report_month]} {self.report_year}'

    def __repr__(self):
        return f'<StudentReport {self.student_id} {self.report_month}/{self.report_year}>'
