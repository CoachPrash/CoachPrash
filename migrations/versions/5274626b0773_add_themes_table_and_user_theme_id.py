"""add themes table and user theme_id

Revision ID: 5274626b0773
Revises: 6f0c429b41b0
Create Date: 2026-05-20 12:32:29.153162

"""
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = '5274626b0773'
down_revision = '6f0c429b41b0'
branch_labels = None
depends_on = None


def upgrade():
    # Create themes table
    themes_table = op.create_table('themes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color_primary', sa.String(length=7), nullable=False),
        sa.Column('color_secondary', sa.String(length=7), nullable=False),
        sa.Column('color_accent', sa.String(length=7), nullable=False),
        sa.Column('color_bg', sa.String(length=7), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Seed existing palettes
    op.bulk_insert(themes_table, [
        {
            'id': str(uuid.uuid4()), 'name': 'Navy & Gold',
            'color_primary': '#1B365D', 'color_secondary': '#C41E3A',
            'color_accent': '#F4A100', 'color_bg': '#FAFAFA',
            'is_active': True, 'is_default': True, 'display_order': 1,
        },
        {
            'id': str(uuid.uuid4()), 'name': 'Sunshine & Navy',
            'color_primary': '#0C1445', 'color_secondary': '#1D4ED8',
            'color_accent': '#FBBF24', 'color_bg': '#F0F4FF',
            'is_active': True, 'is_default': False, 'display_order': 2,
        },
        {
            'id': str(uuid.uuid4()), 'name': 'Teal Scholar',
            'color_primary': '#0F766E', 'color_secondary': '#1E40AF',
            'color_accent': '#F97316', 'color_bg': '#F0FDFA',
            'is_active': True, 'is_default': False, 'display_order': 3,
        },
        {
            'id': str(uuid.uuid4()), 'name': 'Emerald Campus',
            'color_primary': '#047857', 'color_secondary': '#7C3AED',
            'color_accent': '#FBBF24', 'color_bg': '#ECFDF5',
            'is_active': True, 'is_default': False, 'display_order': 4,
        },
        {
            'id': str(uuid.uuid4()), 'name': 'Blackboard Gold',
            'color_primary': '#1C1C1C', 'color_secondary': '#D4A843',
            'color_accent': '#F5C518', 'color_bg': '#F9F7F2',
            'is_active': True, 'is_default': False, 'display_order': 5,
        },
        {
            'id': str(uuid.uuid4()), 'name': 'Bumblebee',
            'color_primary': '#111111', 'color_secondary': '#E6A817',
            'color_accent': '#FFD43B', 'color_bg': '#FFFDE7',
            'is_active': True, 'is_default': False, 'display_order': 6,
        },
    ])

    # Add theme_id to users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('theme_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key('fk_users_theme_id', 'themes', ['theme_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_theme_id', type_='foreignkey')
        batch_op.drop_column('theme_id')

    op.drop_table('themes')
