"""add_performance_indexes

Revision ID: add_perf_idx
Revises: 96af789a1e18
Create Date: 2026-05-15 18:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'add_perf_idx'
down_revision = '96af789a1e18'
branch_labels = None
depends_on = None


def upgrade():
    # Topic lookup by subject + slug
    op.create_index('ix_topics_subject_slug', 'topics', ['subject_id', 'slug'])
    # Concept lookup by topic + slug
    op.create_index('ix_concepts_topic_slug', 'concepts', ['topic_id', 'slug'])
    # Concept listing filtered by active and ordered
    op.create_index('ix_concepts_topic_active', 'concepts', ['topic_id', 'is_active', 'display_order'])
    # Problem set lookup by concept
    op.create_index('ix_problem_sets_concept', 'problem_sets', ['concept_id', 'is_active'])
    # Blog post listing
    op.create_index('ix_blog_posts_published', 'blog_posts', ['is_published', 'published_at'])
    # Student progress lookup
    op.create_index('ix_student_progress_student', 'student_progress', ['student_id'])
    # Attempt log lookup
    op.create_index('ix_attempt_logs_student', 'attempt_logs', ['student_id', 'attempted_at'])


def downgrade():
    op.drop_index('ix_attempt_logs_student', table_name='attempt_logs')
    op.drop_index('ix_student_progress_student', table_name='student_progress')
    op.drop_index('ix_blog_posts_published', table_name='blog_posts')
    op.drop_index('ix_problem_sets_concept', table_name='problem_sets')
    op.drop_index('ix_concepts_topic_active', table_name='concepts')
    op.drop_index('ix_concepts_topic_slug', table_name='concepts')
    op.drop_index('ix_topics_subject_slug', table_name='topics')
