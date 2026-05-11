from flask import render_template, abort
from app.blueprints.subjects import subjects_bp
from app.models.content import Subject, Topic


@subjects_bp.route('/')
def catalog():
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.display_order).all()
    return render_template('subjects/catalog.html', subjects=subjects)


@subjects_bp.route('/<slug>')
def topic_list(slug):
    subject = Subject.query.filter_by(slug=slug, is_active=True).first_or_404()
    topics = Topic.query.filter_by(
        subject_id=subject.id, is_active=True
    ).order_by(Topic.display_order).all()
    return render_template('subjects/topic_list.html', subject=subject, topics=topics)


@subjects_bp.route('/<subject_slug>/<topic_slug>')
def topic_detail(subject_slug, topic_slug):
    subject = Subject.query.filter_by(slug=subject_slug, is_active=True).first_or_404()
    topic = Topic.query.filter_by(
        subject_id=subject.id, slug=topic_slug, is_active=True
    ).first_or_404()
    concepts = topic.concepts.filter_by(is_active=True).order_by('display_order').all()
    if concepts:
        return render_template(
            'study/coming_soon.html', subject=subject, topic=topic, concepts=concepts
        )
    return render_template(
        'study/coming_soon.html', subject=subject, topic=topic, concepts=[]
    )
