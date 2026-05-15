import uuid
import re
from datetime import datetime, timezone
from app.extensions import db


class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = db.Column(db.String(36), db.ForeignKey('topics.id'), nullable=True)
    subject_id = db.Column(db.String(36), db.ForeignKey('subjects.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    resource_type = db.Column(db.String(30), nullable=False, default='google_slides')
    url = db.Column(db.Text, nullable=False)
    embed_url = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=False, default='')
    access_tier = db.Column(db.String(20), nullable=False, default='free')
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    topic = db.relationship('Topic', backref=db.backref('resources', lazy='dynamic', order_by='Resource.display_order'))
    subject = db.relationship('Subject', backref=db.backref('resources', lazy='dynamic', order_by='Resource.display_order'))

    @staticmethod
    def to_embed_url(sharing_url):
        """Convert a Google sharing URL to an embed URL."""
        if not sharing_url:
            return None
        # Google Slides: extract doc ID and build embed URL
        m = re.search(r'docs\.google\.com/presentation/d/([a-zA-Z0-9_-]+)', sharing_url)
        if m:
            return f'https://docs.google.com/presentation/d/{m.group(1)}/embed?start=false&loop=false'
        # Google Docs
        m = re.search(r'docs\.google\.com/document/d/([a-zA-Z0-9_-]+)', sharing_url)
        if m:
            return f'https://docs.google.com/document/d/{m.group(1)}/preview'
        return None

    def __repr__(self):
        return f'<Resource {self.title}>'
