"""One-time helper: stamp existing production DB at baseline migration.

If the alembic_version table doesn't exist yet (DB was created with
db.create_all() before Flask-Migrate was set up), stamp at revision 0001
so that `flask db upgrade` only runs migration 0002+.

Safe to leave in place — once alembic_version exists, this is a no-op.
"""
import os
import sqlalchemy as sa

db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

if not db_url:
    print('stamp_if_needed: no DATABASE_URL, skipping')
    exit(0)

engine = sa.create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version')"
    ))
    has_alembic = result.scalar()

    if has_alembic:
        print('stamp_if_needed: alembic_version exists, nothing to do')
    else:
        print('stamp_if_needed: stamping existing DB at baseline revision 0001')
        conn.execute(sa.text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(sa.text("INSERT INTO alembic_version (version_num) VALUES ('0001')"))
        conn.commit()
        print('stamp_if_needed: done')

engine.dispose()
