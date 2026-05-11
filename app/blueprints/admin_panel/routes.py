from functools import wraps
from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, current_user
from app.blueprints.admin_panel import admin_bp
from app.blueprints.admin_panel.forms import (
    StudentEditForm, SubjectForm, TopicForm, ConceptForm,
    ProblemSetForm, ProblemForm, AccessCodeForm, BlogPostForm, TestimonialForm,
)
from app.models import (
    Testimonial, BlogPost, ContactMessage,
)
from app.models.user import User
from app.models.content import Subject, Topic, Concept
from app.models.practice import ProblemSet, Problem, Choice, Hint, StepByStepSolution
from app.models.access import AccessCode
from app.extensions import db


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    total_students = User.query.filter_by(role='student').count()
    total_premium = User.query.filter_by(role='student', tier='premium').count()
    total_concepts = Concept.query.filter_by(is_active=True).count()
    total_problems = Problem.query.count()
    recent_students = User.query.filter_by(role='student').order_by(
        User.created_at.desc()
    ).limit(10).all()
    recent_messages = ContactMessage.query.order_by(
        ContactMessage.created_at.desc()
    ).limit(5).all()
    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_premium=total_premium,
        total_concepts=total_concepts,
        total_problems=total_problems,
        recent_students=recent_students,
        recent_messages=recent_messages,
    )


# --- Student Management ---

@admin_bp.route('/students')
@admin_required
def manage_students():
    search = request.args.get('search', '')
    query = User.query.filter_by(role='student')
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )
    students = query.order_by(User.created_at.desc()).all()
    return render_template('admin/manage_students.html', students=students, search=search)


@admin_bp.route('/students/<user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_student(user_id):
    student = db.session.get(User, user_id)
    if not student or student.role != 'student':
        abort(404)
    form = StudentEditForm(obj=student)
    if form.validate_on_submit():
        student.tier = form.tier.data
        student.is_active = form.is_active.data
        db.session.commit()
        flash(f'Student {student.username} updated.', 'success')
        return redirect(url_for('admin_panel.manage_students'))
    return render_template('admin/edit_student.html', form=form, student=student)


# --- Content Management ---

@admin_bp.route('/content')
@admin_required
def manage_content():
    subjects = Subject.query.order_by(Subject.display_order).all()
    return render_template('admin/manage_content.html', subjects=subjects)


@admin_bp.route('/content/subject/new', methods=['GET', 'POST'])
@admin_required
def new_subject():
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject(
            name=form.name.data,
            slug=form.slug.data,
            description=form.description.data or '',
            icon=form.icon.data or '',
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        db.session.add(subject)
        db.session.commit()
        flash(f'Subject "{subject.name}" created.', 'success')
        return redirect(url_for('admin_panel.manage_content'))
    return render_template('admin/form_page.html', form=form, title='New Subject')


@admin_bp.route('/content/subject/<subject_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_subject(subject_id):
    subject = db.session.get(Subject, subject_id)
    if not subject:
        abort(404)
    form = SubjectForm(obj=subject)
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.slug = form.slug.data
        subject.description = form.description.data or ''
        subject.icon = form.icon.data or ''
        subject.display_order = form.display_order.data
        subject.is_active = form.is_active.data
        db.session.commit()
        flash(f'Subject "{subject.name}" updated.', 'success')
        return redirect(url_for('admin_panel.manage_content'))
    return render_template('admin/form_page.html', form=form, title=f'Edit Subject: {subject.name}')


@admin_bp.route('/content/subject/<subject_id>/delete', methods=['POST'])
@admin_required
def delete_subject(subject_id):
    subject = db.session.get(Subject, subject_id)
    if not subject:
        abort(404)
    db.session.delete(subject)
    db.session.commit()
    flash(f'Subject "{subject.name}" deleted.', 'success')
    return redirect(url_for('admin_panel.manage_content'))


@admin_bp.route('/content/subject/<subject_id>/topic/new', methods=['GET', 'POST'])
@admin_required
def new_topic(subject_id):
    subject = db.session.get(Subject, subject_id)
    if not subject:
        abort(404)
    form = TopicForm()
    if form.validate_on_submit():
        topic = Topic(
            subject_id=subject.id,
            name=form.name.data,
            slug=form.slug.data,
            description=form.description.data or '',
            difficulty_level=form.difficulty_level.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        db.session.add(topic)
        db.session.commit()
        flash(f'Topic "{topic.name}" created.', 'success')
        return redirect(url_for('admin_panel.manage_content'))
    return render_template(
        'admin/form_page.html', form=form, title=f'New Topic in {subject.name}'
    )


@admin_bp.route('/content/topic/<topic_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_topic(topic_id):
    topic = db.session.get(Topic, topic_id)
    if not topic:
        abort(404)
    form = TopicForm(obj=topic)
    if form.validate_on_submit():
        topic.name = form.name.data
        topic.slug = form.slug.data
        topic.description = form.description.data or ''
        topic.difficulty_level = form.difficulty_level.data
        topic.display_order = form.display_order.data
        topic.is_active = form.is_active.data
        db.session.commit()
        flash(f'Topic "{topic.name}" updated.', 'success')
        return redirect(url_for('admin_panel.manage_content'))
    return render_template('admin/form_page.html', form=form, title=f'Edit Topic: {topic.name}')


@admin_bp.route('/content/topic/<topic_id>/delete', methods=['POST'])
@admin_required
def delete_topic(topic_id):
    topic = db.session.get(Topic, topic_id)
    if not topic:
        abort(404)
    db.session.delete(topic)
    db.session.commit()
    flash('Topic deleted.', 'success')
    return redirect(url_for('admin_panel.manage_content'))


@admin_bp.route('/content/topic/<topic_id>/concept/new', methods=['GET', 'POST'])
@admin_required
def new_concept(topic_id):
    topic = db.session.get(Topic, topic_id)
    if not topic:
        abort(404)
    form = ConceptForm()
    if form.validate_on_submit():
        concept = Concept(
            topic_id=topic.id,
            title=form.title.data,
            slug=form.slug.data,
            content_raw=form.content_raw.data or '',
            content_html=form.content_raw.data or '',
            estimated_minutes=form.estimated_minutes.data,
            access_tier=form.access_tier.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        db.session.add(concept)
        db.session.commit()
        flash(f'Concept "{concept.title}" created.', 'success')
        return redirect(url_for('admin_panel.manage_content'))
    return render_template(
        'admin/form_page.html', form=form, title=f'New Concept in {topic.name}', has_preview=True
    )


@admin_bp.route('/content/concept/<concept_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_concept(concept_id):
    concept = db.session.get(Concept, concept_id)
    if not concept:
        abort(404)
    form = ConceptForm(obj=concept)
    if form.validate_on_submit():
        concept.title = form.title.data
        concept.slug = form.slug.data
        concept.content_raw = form.content_raw.data or ''
        concept.content_html = form.content_raw.data or ''
        concept.estimated_minutes = form.estimated_minutes.data
        concept.access_tier = form.access_tier.data
        concept.display_order = form.display_order.data
        concept.is_active = form.is_active.data
        db.session.commit()
        flash(f'Concept "{concept.title}" updated.', 'success')
        return redirect(url_for('admin_panel.manage_content'))
    return render_template(
        'admin/form_page.html', form=form, title=f'Edit Concept: {concept.title}', has_preview=True
    )


@admin_bp.route('/content/concept/<concept_id>/delete', methods=['POST'])
@admin_required
def delete_concept(concept_id):
    concept = db.session.get(Concept, concept_id)
    if not concept:
        abort(404)
    db.session.delete(concept)
    db.session.commit()
    flash('Concept deleted.', 'success')
    return redirect(url_for('admin_panel.manage_content'))


# --- Access Codes ---

@admin_bp.route('/codes')
@admin_required
def manage_codes():
    codes = AccessCode.query.order_by(AccessCode.created_at.desc()).all()
    return render_template('admin/manage_codes.html', codes=codes)


@admin_bp.route('/codes/new', methods=['GET', 'POST'])
@admin_required
def new_code():
    form = AccessCodeForm()
    if form.validate_on_submit():
        code_str = form.code.data.upper() if form.code.data else AccessCode.generate_code()
        code = AccessCode(
            code=code_str,
            tier=form.tier.data,
            max_uses=form.max_uses.data if form.max_uses.data else None,
            expires_at=form.expires_at.data,
            created_by=current_user.id,
        )
        db.session.add(code)
        db.session.commit()
        flash(f'Access code "{code.code}" created.', 'success')
        return redirect(url_for('admin_panel.manage_codes'))
    return render_template('admin/form_page.html', form=form, title='New Access Code')


@admin_bp.route('/codes/<code_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_code(code_id):
    code = db.session.get(AccessCode, code_id)
    if not code:
        abort(404)
    code.is_active = not code.is_active
    db.session.commit()
    status = 'activated' if code.is_active else 'deactivated'
    flash(f'Access code "{code.code}" {status}.', 'success')
    return redirect(url_for('admin_panel.manage_codes'))


# --- Blog ---

@admin_bp.route('/blog')
@admin_required
def manage_blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/manage_blog.html', posts=posts)


@admin_bp.route('/blog/new', methods=['GET', 'POST'])
@admin_required
def new_blog_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        post = BlogPost(
            author_id=current_user.id,
            title=form.title.data,
            slug=form.slug.data,
            content_raw=form.content_raw.data or '',
            content_html=form.content_raw.data or '',
            excerpt=form.excerpt.data or '',
            is_published=form.is_published.data,
            published_at=datetime.now(timezone.utc) if form.is_published.data else None,
        )
        db.session.add(post)
        db.session.commit()
        flash(f'Blog post "{post.title}" created.', 'success')
        return redirect(url_for('admin_panel.manage_blog'))
    return render_template('admin/form_page.html', form=form, title='New Blog Post', has_preview=True)


@admin_bp.route('/blog/<post_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_blog_post(post_id):
    post = db.session.get(BlogPost, post_id)
    if not post:
        abort(404)
    form = BlogPostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.slug = form.slug.data
        post.content_raw = form.content_raw.data or ''
        post.content_html = form.content_raw.data or ''
        post.excerpt = form.excerpt.data or ''
        was_published = post.is_published
        post.is_published = form.is_published.data
        if form.is_published.data and not was_published:
            post.published_at = datetime.now(timezone.utc)
        db.session.commit()
        flash(f'Blog post "{post.title}" updated.', 'success')
        return redirect(url_for('admin_panel.manage_blog'))
    return render_template(
        'admin/form_page.html', form=form, title=f'Edit Post: {post.title}', has_preview=True
    )


@admin_bp.route('/blog/<post_id>/delete', methods=['POST'])
@admin_required
def delete_blog_post(post_id):
    post = db.session.get(BlogPost, post_id)
    if not post:
        abort(404)
    db.session.delete(post)
    db.session.commit()
    flash('Blog post deleted.', 'success')
    return redirect(url_for('admin_panel.manage_blog'))


# --- Testimonials ---

@admin_bp.route('/testimonials')
@admin_required
def manage_testimonials():
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/manage_testimonials.html', testimonials=testimonials)


@admin_bp.route('/testimonials/new', methods=['GET', 'POST'])
@admin_required
def new_testimonial():
    form = TestimonialForm()
    if form.validate_on_submit():
        testimonial = Testimonial(
            student_name=form.student_name.data,
            student_grade=form.student_grade.data or None,
            content=form.content.data,
            rating=form.rating.data,
            is_featured=form.is_featured.data,
            is_active=form.is_active.data,
        )
        db.session.add(testimonial)
        db.session.commit()
        flash('Testimonial created.', 'success')
        return redirect(url_for('admin_panel.manage_testimonials'))
    return render_template('admin/form_page.html', form=form, title='New Testimonial')


@admin_bp.route('/testimonials/<testimonial_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_testimonial(testimonial_id):
    testimonial = db.session.get(Testimonial, testimonial_id)
    if not testimonial:
        abort(404)
    form = TestimonialForm(obj=testimonial)
    if form.validate_on_submit():
        testimonial.student_name = form.student_name.data
        testimonial.student_grade = form.student_grade.data or None
        testimonial.content = form.content.data
        testimonial.rating = form.rating.data
        testimonial.is_featured = form.is_featured.data
        testimonial.is_active = form.is_active.data
        db.session.commit()
        flash('Testimonial updated.', 'success')
        return redirect(url_for('admin_panel.manage_testimonials'))
    return render_template(
        'admin/form_page.html', form=form, title=f'Edit Testimonial: {testimonial.student_name}'
    )


@admin_bp.route('/testimonials/<testimonial_id>/delete', methods=['POST'])
@admin_required
def delete_testimonial(testimonial_id):
    testimonial = db.session.get(Testimonial, testimonial_id)
    if not testimonial:
        abort(404)
    db.session.delete(testimonial)
    db.session.commit()
    flash('Testimonial deleted.', 'success')
    return redirect(url_for('admin_panel.manage_testimonials'))


# --- Contact Messages ---

@admin_bp.route('/messages')
@admin_required
def manage_messages():
    messages = ContactMessage.query.order_by(
        ContactMessage.is_read.asc(), ContactMessage.created_at.desc()
    ).all()
    return render_template('admin/manage_messages.html', messages=messages)


@admin_bp.route('/messages/<message_id>')
@admin_required
def view_message(message_id):
    message = db.session.get(ContactMessage, message_id)
    if not message:
        abort(404)
    if not message.is_read:
        message.is_read = True
        db.session.commit()
    return render_template('admin/view_message.html', message=message)
