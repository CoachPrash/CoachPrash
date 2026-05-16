import os
from flask import Flask, render_template, request
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

    from app.extensions import db, migrate, login_manager, csrf, oauth, limiter
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    csrf.init_app(flask_app)
    oauth.init_app(flask_app)
    limiter.init_app(flask_app)

    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    from app.models import (  # noqa: F401 — ensure models are registered
        User, Subject, Topic, Concept, ProblemSet, Problem, Choice, Hint,
        StepByStepSolution, StudentProgress, AttemptLog, AccessCode,
        Testimonial, BlogPost, ContactMessage, Resource,
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

    from app.utils.access import register_access_helpers
    register_access_helpers(flask_app)

    from app.utils.bucket_filter import register_bucket_filter
    register_bucket_filter(flask_app)

    @flask_app.context_processor
    def inject_sidebar_subjects():
        try:
            from app.models.content import Subject
            subjects = Subject.query.filter_by(is_active=True).order_by(Subject.display_order).all()
            return dict(sidebar_subjects=subjects)
        except Exception:
            return dict(sidebar_subjects=[])

    # --- Error handlers ---
    @flask_app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @flask_app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @flask_app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # --- Security headers ---
    @flask_app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://*.railway.app; "
            "connect-src 'self'; "
            "frame-src 'self' https://docs.google.com;"
        )
        # Cache-Control for static assets
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response

    _register_cli(flask_app)

    return flask_app


def _register_cli(flask_app):
    @flask_app.cli.command('seed')
    def seed_command():
        """Seed the database with initial data."""
        from seed import run_seed
        run_seed()
