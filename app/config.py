import os


def _fix_db_uri(uri):
    """Railway Postgres URLs use postgres:// which SQLAlchemy rejects."""
    if uri and uri.startswith('postgres://'):
        return uri.replace('postgres://', 'postgresql://', 1)
    return uri


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = _fix_db_uri(
        os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/coachprash')
    )
    WTF_CSRF_ENABLED = True
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    ASSET_VERSION = os.environ.get('ASSET_VERSION', '3.0')
    RATELIMIT_STORAGE_URI = 'memory://'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


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
