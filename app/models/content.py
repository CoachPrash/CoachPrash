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

    courses = db.relationship('Course', backref='subject', lazy='dynamic', order_by='Course.display_order', cascade='all, delete-orphan')
    resources = db.relationship('Resource', backref='subject', lazy='dynamic', order_by='Resource.display_order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Subject {self.name}>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    tagline = db.Column(db.String(300), nullable=True)
    difficulty_level = db.Column(db.String(30), nullable=False, default='high_school')
    course_type = db.Column(db.String(30), nullable=False, default='standard')
    course_info = db.Column(db.JSON, nullable=True, default=None)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    topics = db.relationship('Topic', backref='course', lazy='dynamic', order_by='Topic.display_order', cascade='all, delete-orphan')
    resources = db.relationship('Resource', backref='course', lazy='dynamic', order_by='Resource.display_order', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('subject_id', 'slug', name='uq_course_subject_slug'),
    )

    def __repr__(self):
        return f'<Course {self.name}>'


class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    concept_links = db.relationship(
        'TopicConcept', back_populates='topic', lazy='dynamic',
        order_by='TopicConcept.display_order',
        cascade='all, delete-orphan',
    )
    resources = db.relationship('Resource', backref='topic', lazy='dynamic', order_by='Resource.display_order', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('course_id', 'slug', name='uq_topic_course_slug'),
    )

    def __repr__(self):
        return f'<Topic {self.name}>'


class Concept(db.Model):
    __tablename__ = 'concepts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content_html = db.Column(db.Text, nullable=False, default='')
    content_raw = db.Column(db.Text, nullable=False, default='')
    estimated_minutes = db.Column(db.Integer, nullable=False, default=5)
    access_tier = db.Column(db.String(20), nullable=False, default='free')
    is_active = db.Column(db.Boolean, default=True)
    subject_area = db.Column(db.String(50), nullable=True)
    difficulty = db.Column(db.String(20), nullable=False, default='medium')
    tags = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    topic_links = db.relationship('TopicConcept', back_populates='concept', lazy='dynamic', cascade='all')
    resources = db.relationship('Resource', backref='concept', lazy='dynamic', order_by='Resource.display_order', cascade='all, delete-orphan')
    problem_sets = db.relationship('ProblemSet', backref='concept', lazy='dynamic', order_by='ProblemSet.display_order', cascade='all, delete-orphan')
    student_progress = db.relationship('StudentProgress', backref='concept', lazy='dynamic', cascade='all')

    def __repr__(self):
        return f'<Concept {self.title}>'


class TopicConcept(db.Model):
    __tablename__ = 'topic_concepts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = db.Column(db.String(36), db.ForeignKey('topics.id'), nullable=False, index=True)
    concept_id = db.Column(db.String(36), db.ForeignKey('concepts.id'), nullable=False, index=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.UniqueConstraint('topic_id', 'concept_id', name='uq_topic_concept'),
    )

    topic = db.relationship('Topic', back_populates='concept_links')
    concept = db.relationship('Concept', back_populates='topic_links')

    def __repr__(self):
        return f'<TopicConcept {self.topic_id} - {self.concept_id}>'
