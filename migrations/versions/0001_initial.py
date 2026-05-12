"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('contact_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime()),
    )

    op.create_table('subjects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('icon', sa.String(50), nullable=False, server_default=''),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    op.create_table('testimonials',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('student_name', sa.String(100), nullable=False),
        sa.Column('student_grade', sa.String(50)),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_featured', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime()),
    )

    op.create_table('users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('username', sa.String(80), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='student'),
        sa.Column('auth_provider', sa.String(20), nullable=False, server_default='local'),
        sa.Column('google_id', sa.String(255), unique=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('tier', sa.String(20), nullable=False, server_default='free'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_google_id', 'users', ['google_id'])

    op.create_table('access_codes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('code', sa.String(8), unique=True, nullable=False),
        sa.Column('tier', sa.String(20), nullable=False, server_default='premium'),
        sa.Column('max_uses', sa.Integer()),
        sa.Column('current_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('ix_access_codes_code', 'access_codes', ['code'])

    op.create_table('blog_posts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('author_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), unique=True, nullable=False),
        sa.Column('content_html', sa.Text(), nullable=False, server_default=''),
        sa.Column('content_raw', sa.Text(), nullable=False, server_default=''),
        sa.Column('excerpt', sa.String(500), nullable=False, server_default=''),
        sa.Column('is_published', sa.Boolean(), server_default='false'),
        sa.Column('published_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    op.create_table('topics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('subject_id', sa.String(36), sa.ForeignKey('subjects.id'), nullable=False),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('slug', sa.String(150), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('difficulty_level', sa.String(30), nullable=False, server_default='high_school'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.UniqueConstraint('subject_id', 'slug', name='uq_topic_subject_slug'),
    )

    op.create_table('concepts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('topic_id', sa.String(36), sa.ForeignKey('topics.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=False, server_default=''),
        sa.Column('content_raw', sa.Text(), nullable=False, server_default=''),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('access_tier', sa.String(20), nullable=False, server_default='free'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    op.create_table('problem_sets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('concept_id', sa.String(36), sa.ForeignKey('concepts.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('access_tier', sa.String(20), nullable=False, server_default='free'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    op.create_table('student_progress',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('concept_id', sa.String(36), sa.ForeignKey('concepts.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='not_started'),
        sa.Column('mastery_score', sa.Float()),
        sa.Column('last_accessed', sa.DateTime()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.UniqueConstraint('student_id', 'concept_id', name='uq_student_concept'),
    )

    op.create_table('problems',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('problem_set_id', sa.String(36), sa.ForeignKey('problem_sets.id'), nullable=False),
        sa.Column('question_html', sa.Text(), nullable=False, server_default=''),
        sa.Column('question_raw', sa.Text(), nullable=False, server_default=''),
        sa.Column('problem_type', sa.String(20), nullable=False, server_default='mcq'),
        sa.Column('correct_answer', sa.String(500)),
        sa.Column('points', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('difficulty', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    op.create_table('attempt_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('problem_id', sa.String(36), sa.ForeignKey('problems.id'), nullable=False),
        sa.Column('submitted_answer', sa.String(500), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('hints_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('time_spent_seconds', sa.Integer()),
        sa.Column('attempted_at', sa.DateTime()),
    )

    op.create_table('choices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('problem_id', sa.String(36), sa.ForeignKey('problems.id'), nullable=False),
        sa.Column('choice_text', sa.String(500), nullable=False),
        sa.Column('is_correct', sa.Boolean(), server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
    )

    op.create_table('hints',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('problem_id', sa.String(36), sa.ForeignKey('problems.id'), nullable=False),
        sa.Column('hint_text', sa.Text(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_points', sa.Integer(), nullable=False, server_default='0'),
    )

    op.create_table('step_by_step_solutions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('problem_id', sa.String(36), sa.ForeignKey('problems.id'), unique=True, nullable=False),
        sa.Column('steps_json', sa.JSON(), nullable=False),
        sa.Column('access_tier', sa.String(20), nullable=False, server_default='premium'),
    )


def downgrade():
    op.drop_table('step_by_step_solutions')
    op.drop_table('hints')
    op.drop_table('choices')
    op.drop_table('attempt_logs')
    op.drop_table('problems')
    op.drop_table('student_progress')
    op.drop_table('problem_sets')
    op.drop_table('concepts')
    op.drop_table('topics')
    op.drop_table('blog_posts')
    op.drop_index('ix_access_codes_code', 'access_codes')
    op.drop_table('access_codes')
    op.drop_index('ix_users_google_id', 'users')
    op.drop_index('ix_users_email', 'users')
    op.drop_table('users')
    op.drop_table('testimonials')
    op.drop_table('subjects')
    op.drop_table('contact_messages')
