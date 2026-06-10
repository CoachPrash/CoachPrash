"""drop question_raw from problems

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('problems', schema=None) as batch_op:
        batch_op.drop_column('question_raw')


def downgrade():
    with op.batch_alter_table('problems', schema=None) as batch_op:
        batch_op.add_column(sa.Column('question_raw', sa.Text(), nullable=False, server_default=''))
