import uuid
from datetime import datetime, timezone
from app.extensions import db


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    icon = db.Column(db.String(50), nullable=False, default='')
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    topics = db.relationship('Topic', backref='subject', lazy='dynamic', order_by='Topic.display_order')

    def __repr__(self):
        return f'<Subject {self.name}>'


class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    difficulty_level = db.Column(db.String(30), nullable=False, default='high_school')
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    concepts = db.relationship('Concept', backref='topic', lazy='dynamic', order_by='Concept.display_order')

    __table_args__ = (
        db.UniqueConstraint('subject_id', 'slug', name='uq_topic_subject_slug'),
    )

    def __repr__(self):
        return f'<Topic {self.name}>'


class Concept(db.Model):
    __tablename__ = 'concepts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = db.Column(db.String(36), db.ForeignKey('topics.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    content_html = db.Column(db.Text, nullable=False, default='')
    content_raw = db.Column(db.Text, nullable=False, default='')
    estimated_minutes = db.Column(db.Integer, nullable=False, default=5)
    access_tier = db.Column(db.String(20), nullable=False, default='free')
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    problem_sets = db.relationship('ProblemSet', backref='concept', lazy='dynamic', order_by='ProblemSet.display_order')
    student_progress = db.relationship('StudentProgress', backref='concept', lazy='dynamic')

    def __repr__(self):
        return f'<Concept {self.title}>'
