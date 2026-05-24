import logging
import os
import uuid
from logging.config import dictConfig

from flask import Flask, g, render_template, request, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

load_dotenv()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # Configure logging before creating the app (Flask best practice)
    log_level = 'DEBUG' if config_name == 'development' else 'INFO'
    log_format = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    if config_name == 'production':
        log_format = '%(asctime)s %(levelname)s %(module)s %(message)s'
    dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'format': log_format,
            },
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default',
            },
        },
        'root': {
            'level': log_level,
            'handlers': ['wsgi'],
        },
    })

    flask_app = Flask(__name__)
    if os.environ.get('FLASK_ENV') != 'development':
        flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    from app.config import config as app_config
    config_class = app_config.get(config_name, app_config['default'])
    flask_app.config.from_object(config_class)

    # --- Security: require real secrets in production ---
    if config_name == 'production':
        secret = flask_app.config.get('SECRET_KEY', '')
        if not secret or secret == 'dev-only-not-for-production':
            raise RuntimeError(
                'SECRET_KEY environment variable is required in production'
            )

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
        ParentStudentLink, ParentLinkCode,
        MessageThread, MessageParticipant, Message, StudentReport,
        Theme,
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

    from app.blueprints.parent import parent_bp
    flask_app.register_blueprint(parent_bp, url_prefix='/parent')

    from app.blueprints.messages import messages_bp
    flask_app.register_blueprint(messages_bp, url_prefix='/messages')

    from app.blueprints.settings import settings_bp
    flask_app.register_blueprint(settings_bp, url_prefix='/settings')

    # db.create_all() removed — use Flask-Migrate (flask db upgrade) instead

    from app.utils.access import register_access_helpers
    register_access_helpers(flask_app)

    from app.utils.bucket_filter import register_bucket_filter
    register_bucket_filter(flask_app)

    @flask_app.context_processor
    def inject_unread_messages():
        from flask_login import current_user
        if current_user.is_authenticated:
            from app.models.messaging import Message, MessageParticipant
            count = Message.query.join(
                MessageParticipant,
                Message.thread_id == MessageParticipant.thread_id,
            ).filter(
                MessageParticipant.user_id == current_user.id,
                Message.sender_id != current_user.id,
                Message.is_read == False,  # noqa: E712
            ).count()
            return dict(unread_message_count=count)
        return dict(unread_message_count=0)

    @flask_app.template_filter('nl2br')
    def nl2br_filter(value):
        """Convert newlines to <br> tags for message display."""
        from markupsafe import Markup, escape
        return Markup(escape(value).replace('\n', Markup('<br>')))

    @flask_app.context_processor
    def inject_user_theme():
        from flask_login import current_user
        from app.models.theme import Theme
        from app.utils.colors import derive_palette, palette_to_css_vars
        theme = None
        if current_user.is_authenticated and current_user.theme_id:
            theme = current_user.theme
        if not theme:
            theme = Theme.query.filter_by(is_default=True, is_active=True).first()
        if theme:
            palette = derive_palette(
                theme.color_primary, theme.color_secondary,
                theme.color_accent, theme.color_bg,
            )
            css_vars = palette_to_css_vars(palette)
            return dict(user_theme=theme, theme_css_vars=css_vars)
        return dict(user_theme=None, theme_css_vars=None)

    @flask_app.context_processor
    def inject_sidebar_subjects():
        try:
            from app.models.content import Subject
            subjects = Subject.query.filter_by(is_active=True).order_by(Subject.display_order).all()
            return dict(sidebar_subjects=subjects)
        except Exception:
            flask_app.logger.exception('Failed to load sidebar subjects')
            return dict(sidebar_subjects=[])

    # --- Stealth Mode ---
    @flask_app.before_request
    def stealth_gate():
        stealth_code = os.environ.get('STEALTH_CODE')
        if not stealth_code:
            return None
        allowed = (
            request.path.startswith('/static/')
            or request.path == '/stealth'
            or request.path.startswith('/admin/')
            or request.path.startswith('/auth/')
            or request.path.startswith('/messages/')
        )
        if allowed:
            return None
        if request.cookies.get('stealth') == stealth_code:
            return None
        return redirect('/stealth')

    # --- Request ID for log correlation ---
    @flask_app.before_request
    def set_request_id():
        g.request_id = uuid.uuid4().hex[:12]

    # --- Error handlers ---
    @flask_app.errorhandler(400)
    def bad_request(e):
        flask_app.logger.info('400 Bad Request: %s', request.path)
        return render_template('errors/400.html'), 400

    @flask_app.errorhandler(403)
    def forbidden(e):
        flask_app.logger.warning('403 Forbidden: %s', request.path)
        return render_template('errors/403.html'), 403

    @flask_app.errorhandler(404)
    def page_not_found(e):
        flask_app.logger.info('404 Not Found: %s', request.path)
        return render_template('errors/404.html'), 404

    @flask_app.errorhandler(429)
    def too_many_requests(e):
        flask_app.logger.warning('429 Too Many Requests: %s from %s', request.path, request.remote_addr)
        return render_template('errors/429.html'), 429

    @flask_app.errorhandler(500)
    def internal_error(e):
        flask_app.logger.exception('500 Internal Server Error: %s', request.path)
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # --- Security headers ---
    @flask_app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
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
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), payment=(self)'
        )
        if config_name == 'production':
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )
        # Cache-Control for static assets (production only)
        if request.path.startswith('/static/'):
            if config_name == 'production':
                response.headers['Cache-Control'] = 'public, max-age=31536000'
            else:
                response.headers['Cache-Control'] = 'no-cache'
        return response

    _register_cli(flask_app)

    return flask_app


def _register_cli(flask_app):
    @flask_app.cli.command('seed')
    def seed_command():
        """Seed the database with initial data."""
        from seed import run_seed
        run_seed()
