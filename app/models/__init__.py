from app.models.user import User
from app.models.content import Subject, Topic, Concept
from app.models.practice import ProblemSet, Problem, Choice, Hint, StepByStepSolution
from app.models.progress import StudentProgress, AttemptLog
from app.models.access import AccessCode
from app.models.resource import Resource

from app.extensions import db


class Testimonial(db.Model):
    __tablename__ = 'testimonials'

    id = db.Column(db.String(36), primary_key=True, default=lambda: __import__('uuid').uuid4().__str__())
    student_name = db.Column(db.String(100), nullable=False)
    student_grade = db.Column(db.String(50), nullable=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
    )

    def __repr__(self):
        return f'<Testimonial {self.student_name}>'


class BlogPost(db.Model):
    __tablename__ = 'blog_posts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: __import__('uuid').uuid4().__str__())
    author_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content_html = db.Column(db.Text, nullable=False, default='')
    content_raw = db.Column(db.Text, nullable=False, default='')
    excerpt = db.Column(db.String(500), nullable=False, default='')
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
        onupdate=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
    )

    def __repr__(self):
        return f'<BlogPost {self.title}>'


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: __import__('uuid').uuid4().__str__())
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
    )

    def __repr__(self):
        return f'<ContactMessage from {self.name}>'
