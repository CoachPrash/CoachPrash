"""Railway startup script: ensure DB schema is current and stamp migration head."""
import logging
from app import create_app
from app.extensions import db

logger = logging.getLogger(__name__)


def ensure_schema():
    """Fix stale alembic_version, create missing tables, stamp migration head."""
    app = create_app()
    with app.app_context():
        # Check if alembic_version exists and points to a valid revision
        try:
            result = db.session.execute(
                db.text("SELECT version_num FROM alembic_version")
            ).scalar()
        except Exception:
            result = None
            db.session.rollback()

        if result:
            # Check if the stamped revision exists in our migration files
            import os
            migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations', 'versions')
            revision_exists = any(
                result in f for f in os.listdir(migrations_dir) if f.endswith('.py')
            )
            if revision_exists:
                logger.info("alembic_version OK (revision %s found)", result)
                return
            else:
                logger.warning("Stale alembic_version: %s not found in migrations — resetting", result)
                db.session.execute(db.text("DROP TABLE IF EXISTS alembic_version"))
                db.session.commit()

        # Create all tables from models (idempotent — skips existing tables)
        db.create_all()
        logger.info("db.create_all() complete")

        # Stamp the current migration head so flask db upgrade works on next deploy
        from flask_migrate import stamp
        stamp(revision='head')
        logger.info("Stamped alembic_version to head")


if __name__ == '__main__':
    ensure_schema()
