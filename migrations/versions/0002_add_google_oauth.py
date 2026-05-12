"""add google oauth columns to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('auth_provider', sa.String(20), nullable=False, server_default='local'))
    op.add_column('users', sa.Column('google_id', sa.String(255), unique=True))
    op.create_index('ix_users_google_id', 'users', ['google_id'])
    op.alter_column('users', 'password_hash', existing_type=sa.String(256), nullable=True)


def downgrade():
    op.alter_column('users', 'password_hash', existing_type=sa.String(256), nullable=False)
    op.drop_index('ix_users_google_id', 'users')
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'auth_provider')
