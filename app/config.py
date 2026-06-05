import os
from datetime import timedelta


def _fix_db_uri(uri):
    """Railway Postgres URLs use postgres:// which SQLAlchemy rejects."""
    if uri and uri.startswith('postgres://'):
        return uri.replace('postgres://', 'postgresql://', 1)
    return uri


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-not-for-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = _fix_db_uri(
        os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/coachprash')
    )
    WTF_CSRF_ENABLED = True
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    ASSET_VERSION = os.environ.get('ASSET_VERSION', '11.0')
    RATELIMIT_STORAGE_URI = 'memory://'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_REFRESH_EACH_REQUEST = True
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB upload limit


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # localhost doesn't use HTTPS


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # require HTTPS for cookies


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
