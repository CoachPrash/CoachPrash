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
    theme_id = db.Column(db.String(36), db.ForeignKey('themes.id', ondelete='SET NULL'), nullable=True)
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    theme = db.relationship('Theme', lazy='joined')
    progress = db.relationship('StudentProgress', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    attempts = db.relationship('AttemptLog', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    blog_posts = db.relationship('BlogPost', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    created_codes = db.relationship('AccessCode', backref='creator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    MAX_FAILED_LOGINS = 5
    LOCKOUT_MINUTES = 15

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        return False

    def record_failed_login(self):
        self.failed_login_count = (self.failed_login_count or 0) + 1
        if self.failed_login_count >= self.MAX_FAILED_LOGINS:
            from datetime import timedelta
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=self.LOCKOUT_MINUTES)

    def reset_failed_logins(self):
        self.failed_login_count = 0
        self.locked_until = None

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_premium(self):
        return self.tier == 'premium'

    @property
    def is_parent(self):
        return self.role == 'parent'

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)
