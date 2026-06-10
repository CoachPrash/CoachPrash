"""add access_tier to problems

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('problems', schema=None) as batch_op:
        batch_op.add_column(sa.Column('access_tier', sa.String(20), nullable=False, server_default='free'))


def downgrade():
    with op.batch_alter_table('problems', schema=None) as batch_op:
        batch_op.drop_column('access_tier')
