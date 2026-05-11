import uuid
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='student')
    auth_provider = db.Column(db.String(20), nullable=False, default='local')
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True)
    tier = db.Column(db.String(20), nullable=False, default='free')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    progress = db.relationship('StudentProgress', backref='student', lazy='dynamic')
    attempts = db.relationship('AttemptLog', backref='student', lazy='dynamic')
    blog_posts = db.relationship('BlogPost', backref='author', lazy='dynamic')
    created_codes = db.relationship('AccessCode', backref='creator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_premium(self):
        return self.tier == 'premium'

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)
