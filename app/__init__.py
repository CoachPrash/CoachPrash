import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

load_dotenv()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    flask_app = Flask(__name__)
    flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    from app.config import config as app_config
    config_class = app_config.get(config_name, app_config['default'])
    flask_app.config.from_object(config_class)

    if hasattr(config_class, 'init_app'):
        config_class.init_app(flask_app)

    from app.extensions import db, migrate, login_manager, csrf, oauth
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    csrf.init_app(flask_app)
    oauth.init_app(flask_app)

    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    from app.models import (  # noqa: F401 — ensure models are registered
        User, Subject, Topic, Concept, ProblemSet, Problem, Choice, Hint,
        StepByStepSolution, StudentProgress, AttemptLog, AccessCode,
        Testimonial, BlogPost, ContactMessage,
    )

    from app.blueprints.main import main_bp
    flask_app.register_blueprint(main_bp)

    from app.blueprints.auth import auth_bp
    flask_app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.blueprints.subjects import subjects_bp
    flask_app.register_blueprint(subjects_bp, url_prefix='/subjects')

    from app.blueprints.study import study_bp
    flask_app.register_blueprint(study_bp)

    from app.blueprints.blog import blog_bp
    flask_app.register_blueprint(blog_bp, url_prefix='/resources')

    from app.blueprints.admin_panel import admin_bp
    flask_app.register_blueprint(admin_bp, url_prefix='/admin')

    # db.create_all() removed — use Flask-Migrate (flask db upgrade) instead

    _register_cli(flask_app)

    return flask_app


def _register_cli(flask_app):
    @flask_app.cli.command('seed')
    def seed_command():
        """Seed the database with initial data."""
        from seed import run_seed
        run_seed()
