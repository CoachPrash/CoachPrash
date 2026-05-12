"""Fix alembic_version to point to current revision via raw SQL."""
import os
import sqlalchemy as sa

db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

if not db_url:
    print('fix_alembic: no DATABASE_URL, skipping')
    exit(0)

engine = sa.create_engine(db_url)
with engine.connect() as conn:
    conn.execute(sa.text("DELETE FROM alembic_version"))
    conn.execute(sa.text("INSERT INTO alembic_version (version_num) VALUES ('0001')"))
    conn.commit()
    print('fix_alembic: set alembic_version to 0001')
engine.dispose()
