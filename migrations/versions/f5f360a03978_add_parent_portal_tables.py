"""add parent portal tables

Revision ID: f5f360a03978
Revises: add_perf_idx
Create Date: 2026-05-16 13:18:43.953245

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5f360a03978'
down_revision = 'add_perf_idx'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('parent_link_codes',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('code', sa.String(length=8), nullable=False),
    sa.Column('student_id', sa.String(length=36), nullable=False),
    sa.Column('is_used', sa.Boolean(), nullable=True),
    sa.Column('used_by', sa.String(length=36), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['used_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('parent_link_codes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_parent_link_codes_code'), ['code'], unique=True)

    op.create_table('parent_student_links',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('parent_id', sa.String(length=36), nullable=False),
    sa.Column('student_id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('parent_id', 'student_id', name='uq_parent_student')
    )
    with op.batch_alter_table('parent_student_links', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_parent_student_links_parent_id'), ['parent_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_parent_student_links_student_id'), ['student_id'], unique=False)


def downgrade():
    with op.batch_alter_table('parent_student_links', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_parent_student_links_student_id'))
        batch_op.drop_index(batch_op.f('ix_parent_student_links_parent_id'))

    op.drop_table('parent_student_links')
    with op.batch_alter_table('parent_link_codes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_parent_link_codes_code'))

    op.drop_table('parent_link_codes')
