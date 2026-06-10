import json
import logging
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask import render_template, flash, redirect, url_for, request, abort, jsonify
from flask_login import login_required, current_user
from app.blueprints.admin_panel import admin_bp
from app.blueprints.admin_panel.forms import (
    StudentEditForm, SubjectForm, CourseForm, TopicForm, ConceptForm,
    ProblemSetForm, ProblemForm, AccessCodeForm, BlogPostForm, TestimonialForm,
    ResourceForm, ThemeForm,
)
from app.models import (
    Testimonial, BlogPost, ContactMessage, Resource,
)
from app.models.user import User
from app.models.content import Subject, Course, Topic, Concept, TopicConcept
from app.models.practice import ProblemSet, Problem, Choice, Hint, StepByStepSolution
from app.models.progress import AttemptLog
from app.models.access import AccessCode
from app.models.parent import ParentStudentLink, ParentLinkCode
from app.models.reports import StudentReport
from app.models.theme import Theme
from app.utils.progress import compute_student_stats
from app.utils.colors import derive_palette
from app.extensions import db, limiter
from app.utils.sanitize import sanitize_html
from app.utils.content_loader import _delete_concept_problems

logger = logging.getLogger(__name__)

# Rate limit all admin POST actions (content changes, uploads, etc.)
limiter.limit("30/minute", methods=["POST"])(admin_bp)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            logger.warning('Unauthorized admin access attempt by %s (id=%s) at %s',
                           current_user.username, current_user.id, request.path)
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    total_students = User.query.filter(User.role.in_(['student', 'parent'])).count()
    total_premium = User.query.filter(User.role.in_(['student', 'parent']), User.tier == 'premium').count()
    total_parents = User.query.filter_by(role='parent').count()
    total_concepts = Concept.query.filter_by(is_active=True).count()
    total_problems = Problem.query.count()
    recent_students = User.query.filter_by(role='student').order_by(
        User.created_at.desc()
    ).limit(10).all()
    recent_messages = ContactMessage.query.order_by(
        ContactMessage.created_at.desc()
    ).limit(5).all()

    # Practice analytics
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    attempts_today = AttemptLog.query.filter(AttemptLog.attempted_at >= today_start).count()
    attempts_week = AttemptLog.query.filter(AttemptLog.attempted_at >= week_start).count()
    total_attempts = AttemptLog.query.count()
    correct_attempts = AttemptLog.query.filter_by(is_correct=True).count()
    overall_accuracy = round(correct_attempts / total_attempts * 100, 1) if total_attempts > 0 else 0

    # Most attempted problems (top 5)
    most_attempted = db.session.query(
        Problem.id, Problem.question_html,
        db.func.count(AttemptLog.id).label('attempt_count')
    ).join(AttemptLog, AttemptLog.problem_id == Problem.id
    ).group_by(Problem.id, Problem.question_html
    ).order_by(db.text('attempt_count DESC')
    ).limit(5).all()

    # Hardest problems (lowest accuracy, min 5 attempts)
    hardest = db.session.query(
        Problem.id, Problem.question_html,
        db.func.count(AttemptLog.id).label('attempt_count'),
        db.func.sum(db.case((AttemptLog.is_correct == True, 1), else_=0)).label('correct_count')  # noqa: E712
    ).join(AttemptLog, AttemptLog.problem_id == Problem.id
    ).group_by(Problem.id, Problem.question_html
    ).having(db.func.count(AttemptLog.id) >= 5
    ).all()
    hardest = sorted(hardest, key=lambda r: r.correct_count / r.attempt_count if r.attempt_count else 1)[:5]

    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_premium=total_premium,
        total_concepts=total_concepts,
        total_problems=total_problems,
        recent_students=recent_students,
        recent_messages=recent_messages,
        attempts_today=attempts_today,
        attempts_week=attempts_week,
        total_attempts=total_attempts,
        overall_accuracy=overall_accuracy,
        most_attempted=most_attempted,
        hardest=hardest,
        total_parents=total_parents,
    )


# --- Student Management ---

@admin_bp.route('/students')
@admin_required
def manage_students():
    search = request.args.get('search', '')
    query = User.query.filter(User.role.in_(['student', 'parent']))
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
    if not student or student.role not in ('student', 'parent'):
        abort(404)
    form = StudentEditForm(obj=student)
    if form.validate_on_submit():
        student.tier = form.tier.data
        student.is_active = form.is_active.data
        db.session.commit()
        logger.info('Student updated by admin: %s (tier=%s, active=%s)',
                    student.username, student.tier, student.is_active)
        flash(f'Student {student.username} updated.', 'success')
        return redirect(url_for('admin_panel.manage_students'))

    # Parent link info for this student
    parent_links = ParentStudentLink.query.filter_by(student_id=student.id).all()
    link_codes = ParentLinkCode.query.filter_by(student_id=student.id)\
        .order_by(ParentLinkCode.created_at.desc()).all()

    return render_template(
        'admin/edit_student.html', form=form, student=student,
        parent_links=parent_links, link_codes=link_codes,
    )


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
        logger.info('Subject created: %s (slug=%s)', subject.name, subject.slug)
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
    logger.info('Subject deleted: %s (id=%s)', subject.name, subject.id)
    db.session.delete(subject)
    db.session.commit()
    flash(f'Subject "{subject.name}" deleted.', 'success')
    return redirect(url_for('admin_panel.manage_content'))


@admin_bp.route('/content/subject/<subject_id>/course/new', methods=['GET', 'POST'])
@admin_required
def new_course(subject_id):
    subject = db.session.get(Subject, subject_id)
    if not subject:
        abort(404)
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            subject_id=subject.id,
            name=form.name.data,
            slug=form.slug.data,
            description=form.description.data or '',
            tagline=form.tagline.data or '',
            difficulty_level=form.difficulty_level.data,
            course_type=form.course_type.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        db.session.add(course)
        db.session.commit()
        logger.info('Course created: %s in %s', course.name, subject.name)
        flash(f'Course "{course.name}" created.', 'success')
        return redirect(url_for('admin_panel.manage_content'))
    return render_template(
        'admin/form_page.html', form=form, title=f'New Course in {subject.name}'
    )


@admin_bp.route('/content/course/<course_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        abort(404)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.name = form.name.data
        course.slug = form.slug.data
        course.description = form.description.data or ''
        course.tagline = form.tagline.data or ''
        course.difficulty_level = form.difficulty_level.data
        course.course_type = form.course_type.data
        course.display_order = form.display_order.data
        course.is_active = form.is_active.data
        db.session.commit()
        flash(f'Course "{course.name}" updated.', 'success')
        return redirect(url_for('admin_panel.manage_content'))
    return render_template('admin/form_page.html', form=form, title=f'Edit Course: {course.name}')


@admin_bp.route('/content/course/<course_id>/delete', methods=['POST'])
@admin_required
def delete_course(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        abort(404)
    logger.info('Course deleted: %s (id=%s)', course.name, course.id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted.', 'success')
    return redirect(url_for('admin_panel.manage_content'))


@admin_bp.route('/content/course/<course_id>/topic/new', methods=['GET', 'POST'])
@admin_required
def new_topic(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        abort(404)
    form = TopicForm()
    if form.validate_on_submit():
        topic = Topic(
            course_id=course.id,
            name=form.name.data,
            slug=form.slug.data,
            description=form.description.data or '',
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        db.session.add(topic)
        db.session.commit()
        logger.info('Topic created: %s in %s', topic.name, course.name)
        flash(f'Topic "{topic.name}" created.', 'success')
        return redirect(url_for('admin_panel.manage_content'))
    return render_template(
        'admin/form_page.html', form=form, title=f'New Topic in {course.name}'
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
    logger.info('Topic deleted: %s (id=%s)', topic.name, topic.id)
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
            title=form.title.data,
            slug=form.slug.data,
            content_raw=form.content_raw.data or '',
            content_html=sanitize_html(form.content_raw.data or ''),
            estimated_minutes=form.estimated_minutes.data,
            access_tier=form.access_tier.data,
            subject_area=form.subject_area.data or None,
            difficulty=form.difficulty.data,
            is_active=form.is_active.data,
        )
        db.session.add(concept)
        db.session.flush()
        # Link to topic
        max_order = db.session.query(db.func.max(TopicConcept.display_order)).filter_by(
            topic_id=topic.id
        ).scalar() or 0
        link = TopicConcept(
            topic_id=topic.id,
            concept_id=concept.id,
            display_order=max_order + 1,
        )
        db.session.add(link)
        db.session.commit()
        logger.info('Concept created: %s and linked to %s', concept.title, topic.name)
        flash(f'Concept "{concept.title}" created and linked to {topic.name}.', 'success')
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
        concept.content_html = sanitize_html(form.content_raw.data or '')
        concept.estimated_minutes = form.estimated_minutes.data
        concept.access_tier = form.access_tier.data
        concept.subject_area = form.subject_area.data or None
        concept.difficulty = form.difficulty.data
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
    logger.info('Concept deleted: %s (id=%s)', concept.title, concept.id)
    # Manually delete topic links (Concept side only has cascade='all', not delete-orphan)
    TopicConcept.query.filter_by(concept_id=concept.id).delete()
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
        logger.info('Access code created: %s (tier=%s)', code.code, code.tier)
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
    logger.info('Access code %s: %s', status, code.code)
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
            content_html=sanitize_html(form.content_raw.data or ''),
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
        post.content_html = sanitize_html(form.content_raw.data or '')
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


# --- Resources ---

@admin_bp.route('/resources')
@admin_required
def manage_resources():
    resources = Resource.query.order_by(Resource.display_order).all()
    subjects = Subject.query.order_by(Subject.display_order).all()
    courses = Course.query.order_by(Course.display_order).all()
    topics = Topic.query.order_by(Topic.display_order).all()
    return render_template(
        'admin/manage_resources.html',
        resources=resources, subjects=subjects, courses=courses, topics=topics,
    )


@admin_bp.route('/resources/new', methods=['GET', 'POST'])
@admin_required
def new_resource():
    form = ResourceForm()
    subjects = Subject.query.order_by(Subject.display_order).all()
    courses = Course.query.order_by(Course.display_order).all()
    topics = Topic.query.order_by(Topic.display_order).all()
    concepts = Concept.query.filter_by(is_active=True).order_by(Concept.title).all()

    if form.validate_on_submit():
        subject_id = request.form.get('subject_id') or None
        course_id = request.form.get('course_id') or None
        topic_id = request.form.get('topic_id') or None
        concept_id = request.form.get('concept_id') or None
        if not topic_id and not subject_id and not concept_id and not course_id:
            flash('Select a subject, course, topic, or concept to attach this resource to.', 'danger')
            return render_template(
                'admin/resource_form.html', form=form, title='New Resource',
                subjects=subjects, courses=courses, topics=topics, concepts=concepts,
            )

        embed_url = Resource.to_embed_url(form.url.data)
        resource = Resource(
            subject_id=subject_id,
            course_id=course_id,
            topic_id=topic_id,
            concept_id=concept_id,
            title=form.title.data,
            resource_type=form.resource_type.data,
            url=form.url.data,
            embed_url=embed_url,
            description=form.description.data or '',
            access_tier=form.access_tier.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        db.session.add(resource)
        db.session.commit()
        flash(f'Resource "{resource.title}" created.', 'success')
        return redirect(url_for('admin_panel.manage_resources'))

    return render_template(
        'admin/resource_form.html', form=form, title='New Resource',
        subjects=subjects, courses=courses, topics=topics, concepts=concepts,
    )


@admin_bp.route('/resources/<resource_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if not resource:
        abort(404)
    form = ResourceForm(obj=resource)
    subjects = Subject.query.order_by(Subject.display_order).all()
    courses = Course.query.order_by(Course.display_order).all()
    topics = Topic.query.order_by(Topic.display_order).all()
    concepts = Concept.query.filter_by(is_active=True).order_by(Concept.title).all()

    if form.validate_on_submit():
        subject_id = request.form.get('subject_id') or None
        course_id = request.form.get('course_id') or None
        topic_id = request.form.get('topic_id') or None
        concept_id = request.form.get('concept_id') or None
        if not topic_id and not subject_id and not concept_id and not course_id:
            flash('Select a subject, course, topic, or concept to attach this resource to.', 'danger')
            return render_template(
                'admin/resource_form.html', form=form, title=f'Edit Resource: {resource.title}',
                subjects=subjects, courses=courses, topics=topics, concepts=concepts, resource=resource,
            )

        resource.subject_id = subject_id
        resource.course_id = course_id
        resource.topic_id = topic_id
        resource.concept_id = concept_id
        resource.title = form.title.data
        resource.resource_type = form.resource_type.data
        resource.url = form.url.data
        resource.embed_url = Resource.to_embed_url(form.url.data)
        resource.description = form.description.data or ''
        resource.access_tier = form.access_tier.data
        resource.display_order = form.display_order.data
        resource.is_active = form.is_active.data
        db.session.commit()
        flash(f'Resource "{resource.title}" updated.', 'success')
        return redirect(url_for('admin_panel.manage_resources'))

    return render_template(
        'admin/resource_form.html', form=form, title=f'Edit Resource: {resource.title}',
        subjects=subjects, courses=courses, topics=topics, concepts=concepts, resource=resource,
    )


@admin_bp.route('/resources/<resource_id>/delete', methods=['POST'])
@admin_required
def delete_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if not resource:
        abort(404)
    db.session.delete(resource)
    db.session.commit()
    flash('Resource deleted.', 'success')
    return redirect(url_for('admin_panel.manage_resources'))


# --- Image Upload ---

@admin_bp.route('/images', methods=['GET', 'POST'])
@admin_required
def upload_image():
    from app.utils.storage import upload_file, list_files

    from werkzeug.utils import secure_filename

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.svg'}
    ALLOWED_MIMETYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'image/svg+xml',
    }

    uploaded_key = None
    error = None

    if request.method == 'POST':
        file = request.files.get('image')
        if not file or not file.filename:
            error = 'No file selected.'
        else:
            filename = secure_filename(file.filename)
            if not filename:
                error = 'Invalid filename.'
            else:
                ext = ('.' + filename.rsplit('.', 1)[-1].lower()) if '.' in filename else ''
                if ext not in ALLOWED_EXTENSIONS:
                    error = f'File type not allowed. Accepted: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
                elif file.content_type not in ALLOWED_MIMETYPES:
                    error = f'MIME type not allowed: {file.content_type}'
                else:
                    subject_slug = request.form.get('subject_slug', 'general')
                    course_slug = request.form.get('course_slug', 'general')
                    bucket_key = f'images/{subject_slug}/{course_slug}/{filename}'
                    try:
                        upload_file(file, bucket_key, content_type=file.content_type)
                        uploaded_key = bucket_key
                        logger.info('Image uploaded: %s by %s', bucket_key, current_user.username)
                        flash(f'Image uploaded. Bucket key: {bucket_key}', 'success')
                    except Exception as e:
                        logger.exception('Image upload failed for %s', bucket_key)
                        error = f'Upload failed: {e}'

    # List existing images
    images = []
    try:
        images = list_files(prefix='images/')
    except Exception:
        logger.exception('Failed to list bucket images')

    subjects = Subject.query.order_by(Subject.name).all()
    courses = Course.query.order_by(Course.name).all()

    return render_template(
        'admin/upload_image.html',
        uploaded_key=uploaded_key, error=error, images=images,
        subjects=subjects, courses=courses,
    )


# --- Bulk Import ---

@admin_bp.route('/content/validate-json', methods=['POST'])
@admin_required
def validate_json():
    """AJAX endpoint to validate qhsJSON before import."""
    raw = request.form.get('json_data', '')
    if not raw.strip():
        return jsonify({'valid': False, 'error': 'No JSON data provided.'})

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return jsonify({'valid': False, 'error': f'Invalid JSON: {e}'})

    errors = []
    if not data.get('subject_slug'):
        errors.append('Missing subject_slug')
    if not data.get('course_slug'):
        errors.append('Missing course_slug')

    topics = data.get('topics', [])
    if not topics:
        errors.append('No topics found')

    total_concepts = 0
    total_problems = 0
    for ti, t in enumerate(topics):
        if not t.get('name') and not t.get('slug'):
            errors.append(f'Topic {ti + 1}: missing name/slug')
        for ci, c in enumerate(t.get('concepts', [])):
            total_concepts += 1
            if not c.get('title'):
                errors.append(f'Topic {ti + 1}, Concept {ci + 1}: missing title')
            for psi, ps in enumerate(c.get('problem_sets', [])):
                for pi, p in enumerate(ps.get('problems', [])):
                    total_problems += 1
                    ptype = p.get('problem_type', 'mcq')
                    if ptype not in ('mcq', 'ftb', 'frq'):
                        errors.append(f'Topic {ti + 1}, Concept {ci + 1}, PS {psi + 1}, Problem {pi + 1}: invalid problem_type "{ptype}"')
                    if ptype == 'mcq' and not p.get('choices'):
                        errors.append(f'Topic {ti + 1}, Concept {ci + 1}, PS {psi + 1}, Problem {pi + 1}: MCQ missing choices')
                    if ptype == 'ftb' and not p.get('correct_answer'):
                        errors.append(f'Topic {ti + 1}, Concept {ci + 1}, PS {psi + 1}, Problem {pi + 1}: FTB missing correct_answer')

    if errors:
        return jsonify({'valid': False, 'errors': errors})

    # Check subject/course exist
    subject = Subject.query.filter_by(slug=data['subject_slug']).first()
    if not subject:
        return jsonify({'valid': False, 'error': f'Subject "{data["subject_slug"]}" not found in DB.'})
    course = Course.query.filter_by(subject_id=subject.id, slug=data['course_slug']).first()
    if not course:
        return jsonify({'valid': False, 'error': f'Course "{data["course_slug"]}" not found in {subject.name}.'})

    summary = f'{len(topics)} topic(s), {total_concepts} concept(s), {total_problems} problem(s)'
    return jsonify({'valid': True, 'summary': summary, 'subject': subject.name, 'course': course.name})


@admin_bp.route('/content/import', methods=['GET', 'POST'])
@admin_required
def bulk_import():
    if request.method == 'GET':
        return render_template('admin/bulk_import.html')

    # Handle JSON from textarea or file upload
    raw = ''
    if request.files.get('json_file') and request.files['json_file'].filename:
        raw = request.files['json_file'].read().decode('utf-8')
    elif request.form.get('json_data'):
        raw = request.form['json_data']

    if not raw.strip():
        flash('No JSON data provided.', 'danger')
        return render_template('admin/bulk_import.html')

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning('Bulk import — invalid JSON: %s', e)
        flash(f'Invalid JSON: {e}', 'danger')
        return render_template('admin/bulk_import.html')

    # Validate structure
    subject_slug = data.get('subject_slug')
    course_slug = data.get('course_slug')
    if not subject_slug or not course_slug:
        flash('JSON must include subject_slug and course_slug.', 'danger')
        return render_template('admin/bulk_import.html')

    subject = Subject.query.filter_by(slug=subject_slug).first()
    if not subject:
        flash(f'Subject "{subject_slug}" not found.', 'danger')
        return render_template('admin/bulk_import.html')

    course = Course.query.filter_by(subject_id=subject.id, slug=course_slug).first()
    if not course:
        flash(f'Course "{course_slug}" not found in {subject.name}.', 'danger')
        return render_template('admin/bulk_import.html')

    topics_data = data.get('topics', [])
    if not topics_data:
        flash('No topics found in JSON.', 'danger')
        return render_template('admin/bulk_import.html')

    # Import within a transaction
    counts = {'topics': 0, 'concepts': 0, 'problem_sets': 0, 'problems': 0,
              'choices': 0, 'hints': 0, 'solutions': 0}
    try:
        for ti, tdata in enumerate(topics_data):
            topic_slug = tdata.get('slug', tdata.get('name', f'topic-{ti+1}').lower().replace(' ', '-'))
            topic = Topic.query.filter_by(course_id=course.id, slug=topic_slug).first()
            if not topic:
                topic = Topic(
                    course_id=course.id,
                    name=tdata.get('name', f'Topic {ti + 1}'),
                    slug=topic_slug,
                    description=tdata.get('description', ''),
                    display_order=tdata.get('display_order', ti),
                    is_active=True,
                )
                db.session.add(topic)
                db.session.flush()
                counts['topics'] += 1
            else:
                topic.name = tdata.get('name', topic.name)
                topic.description = tdata.get('description', topic.description)
                topic.display_order = tdata.get('display_order', ti)

            for ci, cdata in enumerate(tdata.get('concepts', [])):
                slug = cdata.get('slug', cdata.get('title', f'concept-{ci+1}').lower().replace(' ', '-'))
                concept = Concept.query.filter_by(slug=slug).first()
                if concept:
                    # Update existing concept and replace its problems
                    concept.title = cdata.get('title', concept.title)
                    concept.content_html = sanitize_html(cdata.get('content_html', concept.content_html or ''))
                    concept.content_raw = cdata.get('content_raw', concept.content_raw or '')
                    concept.estimated_minutes = cdata.get('estimated_minutes', concept.estimated_minutes)
                    concept.access_tier = cdata.get('access_tier', concept.access_tier)
                    concept.subject_area = cdata.get('subject_area', concept.subject_area)
                    concept.difficulty = cdata.get('difficulty', concept.difficulty)
                    concept.tags = cdata.get('tags', concept.tags)
                    _delete_concept_problems(concept)
                else:
                    concept = Concept(
                        title=cdata.get('title', f'Concept {ci + 1}'),
                        slug=slug,
                        content_html=sanitize_html(cdata.get('content_html', cdata.get('content_raw', ''))),
                        content_raw=cdata.get('content_raw', ''),
                        estimated_minutes=cdata.get('estimated_minutes', 5),
                        access_tier=cdata.get('access_tier', 'free'),
                        subject_area=cdata.get('subject_area'),
                        difficulty=cdata.get('difficulty', 'medium'),
                        tags=cdata.get('tags', []),
                        is_active=True,
                    )
                    db.session.add(concept)
                    db.session.flush()
                counts['concepts'] += 1

                for psi, psdata in enumerate(cdata.get('problem_sets', [])):
                    ps = ProblemSet(
                        concept_id=concept.id,
                        title=psdata.get('title', f'Problem Set {psi + 1}'),
                        access_tier=psdata.get('access_tier', 'free'),
                        display_order=psdata.get('display_order', psi),
                        is_active=True,
                    )
                    db.session.add(ps)
                    db.session.flush()
                    counts['problem_sets'] += 1

                    for pi, pdata in enumerate(psdata.get('problems', [])):
                        problem_type = pdata.get('problem_type', 'mcq')
                        if problem_type not in ('mcq', 'ftb', 'frq'):
                            problem_type = 'mcq'
                        problem = Problem(
                            problem_set_id=ps.id,
                            question_html=sanitize_html(pdata.get('question_html', '')),
                            problem_type=problem_type,
                            correct_answer=pdata.get('correct_answer', ''),
                            difficulty=pdata.get('difficulty', 'medium'),
                            points=pdata.get('points', 1),
                            display_order=pdata.get('display_order', pi),
                        )
                        db.session.add(problem)
                        db.session.flush()
                        counts['problems'] += 1

                        for chi, chdata in enumerate(pdata.get('choices', [])):
                            choice = Choice(
                                problem_id=problem.id,
                                choice_text=chdata.get('text', chdata.get('choice_text', '')),
                                is_correct=chdata.get('is_correct', False),
                                display_order=chi,
                            )
                            db.session.add(choice)
                            counts['choices'] += 1

                        for hi, hdata in enumerate(pdata.get('hints', [])):
                            hint_text = hdata if isinstance(hdata, str) else hdata.get('text', hdata.get('hint_text', ''))
                            cost = 0 if isinstance(hdata, str) else hdata.get('cost_points', 0)
                            hint = Hint(
                                problem_id=problem.id,
                                hint_text=hint_text,
                                display_order=hi,
                                cost_points=cost,
                            )
                            db.session.add(hint)
                            counts['hints'] += 1

                        solution_data = pdata.get('solution_steps', pdata.get('solution'))
                        if solution_data:
                            if isinstance(solution_data, list):
                                steps = []
                                for i, s in enumerate(solution_data):
                                    if isinstance(s, str):
                                        steps.append({'step_number': i + 1, 'text_html': s})
                                    else:
                                        steps.append({
                                            'step_number': s.get('step_number', i + 1),
                                            'text_html': s.get('text', s.get('text_html', '')),
                                        })
                            elif isinstance(solution_data, dict):
                                steps = solution_data.get('steps_json', [])
                            else:
                                steps = []
                            if steps:
                                sol = StepByStepSolution(
                                    problem_id=problem.id,
                                    steps_json=steps,
                                    access_tier=pdata.get('solution', {}).get('access_tier', 'premium')
                                    if isinstance(pdata.get('solution'), dict) else 'premium',
                                )
                                db.session.add(sol)
                                counts['solutions'] += 1

                # Link concept to topic via TopicConcept
                existing_link = TopicConcept.query.filter_by(
                    topic_id=topic.id, concept_id=concept.id
                ).first()
                if not existing_link:
                    link = TopicConcept(
                        topic_id=topic.id,
                        concept_id=concept.id,
                        display_order=cdata.get('display_order', ci),
                    )
                    db.session.add(link)

        db.session.commit()
        logger.info('Bulk import successful: %s topics, %s concepts, %s problems into %s/%s',
                    counts['topics'], counts['concepts'], counts['problems'],
                    subject.name, course.name)
        flash(
            f"Import successful: {counts['topics']} topics, {counts['concepts']} concepts, "
            f"{counts['problem_sets']} problem sets, {counts['problems']} problems, "
            f"{counts['choices']} choices, {counts['hints']} hints, {counts['solutions']} solutions.",
            'success'
        )
    except Exception as e:
        db.session.rollback()
        logger.exception('Bulk import failed for %s/%s', subject_slug, course_slug)
        flash(f'Import failed: {e}', 'danger')

    return redirect(url_for('admin_panel.bulk_import'))


# --- Seed File Management ---

@admin_bp.route('/seeds')
@admin_required
def manage_seeds():
    import os
    from app.utils.seed_scanner import scan_seed_files
    content_dir = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'content'))
    seed_files = scan_seed_files(content_dir)
    return render_template('admin/manage_seeds.html', seed_files=seed_files)


@admin_bp.route('/seeds/run-full-seed', methods=['POST'])
@admin_required
def run_full_seed():
    try:
        from seed import run_seed
        run_seed()
        flash('Full seed completed successfully.', 'success')
    except Exception as e:
        logger.exception('Error running full seed')
        flash(f'Error running full seed: {e}', 'danger')
    return redirect(url_for('admin_panel.manage_seeds'))


@admin_bp.route('/seeds/reseed', methods=['POST'])
@admin_required
def reseed_file():
    import os
    from app.utils.content_loader import load_content_json
    filename = request.form.get('filename', '').strip()
    if not filename or '/' in filename or '\\' in filename or '..' in filename:
        flash('Invalid filename.', 'danger')
        return redirect(url_for('admin_panel.manage_seeds'))

    content_dir = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'content'))
    filepath = os.path.join(content_dir, filename)

    if not os.path.isfile(filepath):
        flash(f'Seed file not found: {filename}', 'danger')
        return redirect(url_for('admin_panel.manage_seeds'))

    try:
        result = load_content_json(filepath)
        flash(
            f'Reseeded {filename}: {result["topics"]} topics, '
            f'{result["concepts"]} concepts, {result["problems"]} problems.',
            'success',
        )
    except Exception as e:
        logger.exception('Error reseeding %s', filename)
        flash(f'Error reseeding {filename}: {e}', 'danger')

    return redirect(url_for('admin_panel.manage_seeds'))


# --- Problem Set & Problem Editor ---

@admin_bp.route('/content/concept/<concept_id>/problem-set/new', methods=['GET', 'POST'])
@admin_required
def new_problem_set(concept_id):
    concept = db.session.get(Concept, concept_id)
    if not concept:
        abort(404)
    form = ProblemSetForm()
    if form.validate_on_submit():
        ps = ProblemSet(
            concept_id=concept.id,
            title=form.title.data,
            access_tier=form.access_tier.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        db.session.add(ps)
        db.session.commit()
        logger.info('Problem set created: %s for concept %s', ps.title, concept.title)
        flash(f'Problem set "{ps.title}" created.', 'success')
        return redirect(url_for('admin_panel.problem_set_detail', ps_id=ps.id))
    return render_template('admin/form_page.html', form=form, title=f'New Problem Set for {concept.title}')


@admin_bp.route('/content/problem-set/<ps_id>')
@admin_required
def problem_set_detail(ps_id):
    ps = db.session.get(ProblemSet, ps_id)
    if not ps:
        abort(404)
    concept = db.session.get(Concept, ps.concept_id)
    problems = ps.problems.all()
    ps_form = ProblemSetForm(obj=ps)
    return render_template(
        'admin/problem_set_detail.html',
        ps=ps, concept=concept, problems=problems, ps_form=ps_form,
    )


@admin_bp.route('/content/problem-set/<ps_id>/edit', methods=['POST'])
@admin_required
def edit_problem_set(ps_id):
    ps = db.session.get(ProblemSet, ps_id)
    if not ps:
        abort(404)
    form = ProblemSetForm()
    if form.validate_on_submit():
        ps.title = form.title.data
        ps.access_tier = form.access_tier.data
        ps.display_order = form.display_order.data
        ps.is_active = form.is_active.data
        db.session.commit()
        flash(f'Problem set "{ps.title}" updated.', 'success')
    return redirect(url_for('admin_panel.problem_set_detail', ps_id=ps.id))


@admin_bp.route('/content/problem-set/<ps_id>/delete', methods=['POST'])
@admin_required
def delete_problem_set(ps_id):
    ps = db.session.get(ProblemSet, ps_id)
    if not ps:
        abort(404)
    # Delete attempt logs before cascade delete
    for problem in ps.problems.all():
        AttemptLog.query.filter_by(problem_id=problem.id).delete()
    logger.info('Problem set deleted: %s (id=%s)', ps.title, ps.id)
    db.session.delete(ps)
    db.session.commit()
    flash('Problem set deleted.', 'success')
    return redirect(url_for('admin_panel.manage_content'))


@admin_bp.route('/content/problem-set/<ps_id>/problem/new', methods=['POST'])
@admin_required
def new_problem(ps_id):
    ps = db.session.get(ProblemSet, ps_id)
    if not ps:
        abort(404)
    max_order = db.session.query(db.func.max(Problem.display_order)).filter_by(
        problem_set_id=ps.id
    ).scalar() or 0
    problem = Problem(
        problem_set_id=ps.id,
        question_html='<p>New question</p>',
        problem_type='mcq',
        difficulty='medium',
        points=1,
        display_order=max_order + 1,
    )
    db.session.add(problem)
    db.session.commit()
    flash('New problem added. Edit it below.', 'success')
    return redirect(url_for('admin_panel.problem_set_detail', ps_id=ps.id))


@admin_bp.route('/content/problem/<problem_id>/edit', methods=['POST'])
@admin_required
def edit_problem(problem_id):
    problem = db.session.get(Problem, problem_id)
    if not problem:
        abort(404)

    # Core fields
    problem.question_html = sanitize_html(request.form.get('question_html', ''))
    problem.problem_type = request.form.get('problem_type', 'mcq')
    problem.correct_answer = request.form.get('correct_answer', '')
    problem.difficulty = request.form.get('difficulty', 'medium')
    problem.points = int(request.form.get('points', 1) or 1)
    problem.access_tier = request.form.get('access_tier', 'free')

    # --- Choices (delete and recreate) ---
    Choice.query.filter_by(problem_id=problem.id).delete()
    if problem.problem_type == 'mcq':
        choice_texts = request.form.getlist('choice_text[]')
        correct_idx = request.form.get('correct_choice', '')
        for i, text in enumerate(choice_texts):
            if text.strip():
                is_correct = str(i) == correct_idx
                choice = Choice(
                    problem_id=problem.id,
                    choice_text=text.strip(),
                    is_correct=is_correct,
                    display_order=i,
                )
                db.session.add(choice)
                if is_correct:
                    problem.correct_answer = text.strip()

    # --- Hints (delete and recreate) ---
    Hint.query.filter_by(problem_id=problem.id).delete()
    hint_texts = request.form.getlist('hint_text[]')
    hint_costs = request.form.getlist('hint_cost[]')
    for i, text in enumerate(hint_texts):
        if text.strip():
            cost = int(hint_costs[i]) if i < len(hint_costs) and hint_costs[i] else 0
            hint = Hint(
                problem_id=problem.id,
                hint_text=text.strip(),
                display_order=i,
                cost_points=cost,
            )
            db.session.add(hint)

    # --- Solution Steps (upsert) ---
    step_texts = request.form.getlist('step_text[]')
    steps_json = []
    for i, text in enumerate(step_texts):
        if text.strip():
            steps_json.append({'step_number': i + 1, 'text_html': text.strip()})

    if steps_json:
        sol = StepByStepSolution.query.filter_by(problem_id=problem.id).first()
        if sol:
            sol.steps_json = steps_json
        else:
            sol = StepByStepSolution(
                problem_id=problem.id,
                steps_json=steps_json,
                access_tier='premium',
            )
            db.session.add(sol)
    else:
        StepByStepSolution.query.filter_by(problem_id=problem.id).delete()

    db.session.commit()
    flash('Problem updated.', 'success')
    return redirect(url_for('admin_panel.problem_set_detail', ps_id=problem.problem_set_id))


@admin_bp.route('/content/problem/<problem_id>/delete', methods=['POST'])
@admin_required
def delete_problem(problem_id):
    problem = db.session.get(Problem, problem_id)
    if not problem:
        abort(404)
    ps_id = problem.problem_set_id
    # Delete attempt logs for this problem
    AttemptLog.query.filter_by(problem_id=problem.id).delete()
    logger.info('Problem deleted: %s', problem.id)
    db.session.delete(problem)
    db.session.commit()
    flash('Problem deleted.', 'success')
    return redirect(url_for('admin_panel.problem_set_detail', ps_id=ps_id))


@admin_bp.route('/content/problem-set/<ps_id>/reorder', methods=['POST'])
@admin_required
def reorder_problems(ps_id):
    ps = db.session.get(ProblemSet, ps_id)
    if not ps:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    if not data or 'problem_ids' not in data:
        return jsonify({'error': 'Missing problem_ids'}), 400
    for i, pid in enumerate(data['problem_ids']):
        problem = db.session.get(Problem, pid)
        if problem and problem.problem_set_id == ps.id:
            problem.display_order = i
    db.session.commit()
    return jsonify({'success': True})


# --- Parent Management ---

@admin_bp.route('/parents')
@admin_required
def manage_parents():
    parents = User.query.filter_by(role='parent').order_by(User.created_at.desc()).all()
    parent_data = []
    for parent in parents:
        links = ParentStudentLink.query.filter_by(parent_id=parent.id).all()
        linked_students = []
        for link in links:
            student = db.session.get(User, link.student_id)
            if student:
                linked_students.append({'student': student, 'link': link})
        parent_data.append({
            'parent': parent,
            'linked_students': linked_students,
        })
    return render_template('admin/manage_parents.html', parent_data=parent_data)


@admin_bp.route('/students/<student_id>/generate-parent-code', methods=['POST'])
@admin_required
def generate_parent_code(student_id):
    student = db.session.get(User, student_id)
    if not student or student.role not in ('student', 'parent'):
        abort(404)
    code = ParentLinkCode.create_for_student(student.id)
    logger.info('Parent link code generated for student %s: %s', student.username, code.code)
    flash(f'Parent link code generated: {code.code} (expires in 7 days)', 'success')
    return redirect(url_for('admin_panel.edit_student', user_id=student_id))


@admin_bp.route('/parent-links/<link_id>/remove', methods=['POST'])
@admin_required
def remove_parent_link(link_id):
    link = db.session.get(ParentStudentLink, link_id)
    if not link:
        abort(404)
    parent = db.session.get(User, link.parent_id)
    logger.info('Parent-student link removed: parent_id=%s, student_id=%s', link.parent_id, link.student_id)
    db.session.delete(link)

    # If parent has no more links, revert role to student
    remaining = ParentStudentLink.query.filter_by(parent_id=link.parent_id).count()
    if remaining == 0 and parent and parent.role == 'parent':
        parent.role = 'student'
        logger.info('User %s role reverted from parent to student (no remaining links)', parent.username)

    db.session.commit()
    flash('Parent-student link removed.', 'success')
    return redirect(url_for('admin_panel.manage_parents'))


# --- Coach Dashboard ---

@admin_bp.route('/coach')
@admin_required
def coach_dashboard():
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'last_active')
    order = request.args.get('order', 'desc')

    query = User.query.filter(User.role.in_(['student', 'parent']), User.is_active == True)  # noqa: E712
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )
    students = query.all()

    now = datetime.now(timezone.utc)
    student_rows = []
    at_risk = []

    for student in students:
        total_attempts = AttemptLog.query.filter_by(student_id=student.id).count()
        correct = AttemptLog.query.filter_by(student_id=student.id, is_correct=True).count()
        accuracy = round((correct / total_attempts * 100), 1) if total_attempts > 0 else 0

        completed = db.session.query(db.func.count()).select_from(
            db.session.query(AttemptLog.student_id).filter_by(student_id=student.id)
            .join(Problem, Problem.id == AttemptLog.problem_id)
        ).scalar() or 0
        from app.models.progress import StudentProgress
        concepts_completed = StudentProgress.query.filter_by(
            student_id=student.id, status='completed'
        ).count()

        last_attempt = AttemptLog.query.filter_by(student_id=student.id)\
            .order_by(AttemptLog.attempted_at.desc()).first()
        last_active = last_attempt.attempted_at if last_attempt else None

        # Streak (simplified: count consecutive days from today)
        streak = 0
        if total_attempts > 0:
            check_date = now.date()
            while True:
                day_start = datetime.combine(check_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                day_end = day_start + timedelta(days=1)
                has = AttemptLog.query.filter(
                    AttemptLog.student_id == student.id,
                    AttemptLog.attempted_at >= day_start,
                    AttemptLog.attempted_at < day_end,
                ).first() is not None
                if has:
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break

        row = {
            'student': student,
            'total_attempts': total_attempts,
            'accuracy': accuracy,
            'concepts_completed': concepts_completed,
            'last_active': last_active,
            'streak': streak,
        }
        student_rows.append(row)

        # At-risk detection
        if total_attempts > 0:
            # Ensure timezone-aware comparison
            la = last_active.replace(tzinfo=timezone.utc) if last_active and last_active.tzinfo is None else last_active
            if la and (now - la).days > 7:
                at_risk.append({**row, 'reason': f'Inactive for {(now - la).days} days'})
            elif total_attempts >= 10 and accuracy < 50:
                at_risk.append({**row, 'reason': f'Low accuracy ({accuracy}%)'})

    # Sort
    def _tz_aware(dt):
        """Ensure a datetime is timezone-aware for safe comparison."""
        if dt is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

    sort_keys = {
        'name': lambda r: r['student'].username.lower(),
        'tier': lambda r: r['student'].tier,
        'last_active': lambda r: _tz_aware(r['last_active']),
        'accuracy': lambda r: r['accuracy'],
        'streak': lambda r: r['streak'],
        'concepts': lambda r: r['concepts_completed'],
    }
    sort_fn = sort_keys.get(sort_by, sort_keys['last_active'])
    student_rows.sort(key=sort_fn, reverse=(order == 'desc'))

    # Class-wide analytics
    thirty_days_ago = now - timedelta(days=30)
    active_students = db.session.query(db.func.count(db.distinct(AttemptLog.student_id))).filter(
        AttemptLog.attempted_at >= thirty_days_ago
    ).scalar() or 0

    total_all_attempts = AttemptLog.query.count()
    total_correct = AttemptLog.query.filter_by(is_correct=True).count()
    avg_accuracy = round(total_correct / total_all_attempts * 100, 1) if total_all_attempts > 0 else 0

    return render_template(
        'admin/coach_dashboard.html',
        student_rows=student_rows,
        at_risk=at_risk,
        search=search,
        sort_by=sort_by,
        order=order,
        active_students=active_students,
        avg_accuracy=avg_accuracy,
        total_student_count=len(student_rows),
    )


@admin_bp.route('/coach/student/<student_id>')
@admin_required
def coach_student_detail(student_id):
    student = db.session.get(User, student_id)
    if not student:
        abort(404)
    stats = compute_student_stats(student.id)
    return render_template(
        'admin/coach_student_detail.html',
        student=student,
        **stats,
    )


# --- Monthly Reports ---

@admin_bp.route('/reports')
@admin_required
def manage_reports():
    reports = StudentReport.query.order_by(StudentReport.created_at.desc()).all()
    students = User.query.filter(User.role.in_(['student', 'parent'])).order_by(User.username).all()
    now = datetime.now(timezone.utc)
    return render_template(
        'admin/manage_reports.html', reports=reports, students=students,
        now_month=now.month, now_year=now.year,
    )


@admin_bp.route('/reports/generate', methods=['POST'])
@admin_required
def generate_report():
    student_id = request.form.get('student_id')
    month = int(request.form.get('month', datetime.now(timezone.utc).month))
    year = int(request.form.get('year', datetime.now(timezone.utc).year))

    student = db.session.get(User, student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin_panel.manage_reports'))

    # Check if report already exists
    existing = StudentReport.query.filter_by(
        student_id=student_id, report_month=month, report_year=year
    ).first()
    if existing:
        flash(f'Report for {existing.period_label} already exists.', 'info')
        return redirect(url_for('admin_panel.view_report', report_id=existing.id))

    # Compute period-specific stats
    period_start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        period_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        period_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    attempts_in_period = AttemptLog.query.filter(
        AttemptLog.student_id == student_id,
        AttemptLog.attempted_at >= period_start,
        AttemptLog.attempted_at < period_end,
    ).count()

    correct_in_period = AttemptLog.query.filter(
        AttemptLog.student_id == student_id,
        AttemptLog.attempted_at >= period_start,
        AttemptLog.attempted_at < period_end,
        AttemptLog.is_correct == True,  # noqa: E712
    ).count()
    period_accuracy = round(correct_in_period / attempts_in_period * 100, 1) if attempts_in_period > 0 else 0

    # Previous month accuracy for trend
    if month == 1:
        prev_start = datetime(year - 1, 12, 1, tzinfo=timezone.utc)
        prev_end = period_start
    else:
        prev_start = datetime(year, month - 1, 1, tzinfo=timezone.utc)
        prev_end = period_start

    prev_attempts = AttemptLog.query.filter(
        AttemptLog.student_id == student_id,
        AttemptLog.attempted_at >= prev_start,
        AttemptLog.attempted_at < prev_end,
    ).count()
    prev_correct = AttemptLog.query.filter(
        AttemptLog.student_id == student_id,
        AttemptLog.attempted_at >= prev_start,
        AttemptLog.attempted_at < prev_end,
        AttemptLog.is_correct == True,  # noqa: E712
    ).count()
    prev_accuracy = round(prev_correct / prev_attempts * 100, 1) if prev_attempts > 0 else None

    # Concepts progress in period
    from app.models.progress import StudentProgress
    concepts_completed = StudentProgress.query.filter(
        StudentProgress.student_id == student_id,
        StudentProgress.status == 'completed',
        StudentProgress.last_accessed >= period_start,
        StudentProgress.last_accessed < period_end,
    ).count()

    concepts_started = StudentProgress.query.filter(
        StudentProgress.student_id == student_id,
        StudentProgress.last_accessed >= period_start,
        StudentProgress.last_accessed < period_end,
    ).count()

    # Per-topic accuracy for strengths/weaknesses
    topic_stats = []
    period_attempts = AttemptLog.query.filter(
        AttemptLog.student_id == student_id,
        AttemptLog.attempted_at >= period_start,
        AttemptLog.attempted_at < period_end,
    ).all()

    topic_data = {}
    for att in period_attempts:
        problem = db.session.get(Problem, att.problem_id)
        if problem and problem.problem_set:
            concept = db.session.get(Concept, problem.problem_set.concept_id)
            if concept:
                # Find topics linked to this concept via TopicConcept
                topic_links = TopicConcept.query.filter_by(concept_id=concept.id).all()
                for tl in topic_links:
                    t = db.session.get(Topic, tl.topic_id)
                    if t:
                        key = t.id
                        if key not in topic_data:
                            topic_data[key] = {'name': t.name, 'total': 0, 'correct': 0}
                        topic_data[key]['total'] += 1
                        if att.is_correct:
                            topic_data[key]['correct'] += 1

    for td in topic_data.values():
        td['accuracy'] = round(td['correct'] / td['total'] * 100, 1) if td['total'] > 0 else 0
        topic_stats.append(td)

    topic_stats.sort(key=lambda t: t['accuracy'], reverse=True)
    strongest = topic_stats[:3] if topic_stats else []
    weakest = list(reversed(topic_stats[-3:])) if len(topic_stats) > 1 else []

    # Auto-generated recommendations
    recommendations = []
    if weakest:
        recommendations.append(f"Focus on {weakest[0]['name']} — accuracy is {weakest[0]['accuracy']}%.")
    if strongest:
        recommendations.append(f"Great work on {strongest[0]['name']} — {strongest[0]['accuracy']}% accuracy!")
    if prev_accuracy is not None:
        diff = period_accuracy - prev_accuracy
        if diff > 0:
            recommendations.append(f"Overall accuracy improved by {diff:.1f}% from last month.")
        elif diff < 0:
            recommendations.append(f"Overall accuracy dropped by {abs(diff):.1f}% from last month — review recent topics.")
    if attempts_in_period == 0:
        recommendations.append("No practice attempts this month — encourage regular practice sessions.")

    summary = {
        'student_name': student.username,
        'student_email': student.email,
        'period_label': f'{["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][month]} {year}',
        'attempts': attempts_in_period,
        'accuracy': period_accuracy,
        'prev_accuracy': prev_accuracy,
        'concepts_started': concepts_started,
        'concepts_completed': concepts_completed,
        'strongest': strongest,
        'weakest': weakest,
        'recommendations': recommendations,
    }

    report = StudentReport(
        student_id=student_id,
        report_month=month,
        report_year=year,
        generated_by=current_user.id,
        summary_json=summary,
    )
    db.session.add(report)
    db.session.commit()
    logger.info('Report generated for student %s: %s %s', student.username, month, year)
    flash(f'Report generated for {summary["period_label"]}.', 'success')
    return redirect(url_for('admin_panel.view_report', report_id=report.id))


@admin_bp.route('/reports/<report_id>')
@admin_required
def view_report(report_id):
    report = db.session.get(StudentReport, report_id)
    if not report:
        abort(404)
    return render_template('admin/view_report.html', report=report)


@admin_bp.route('/reports/<report_id>/pdf')
@admin_required
def download_report_pdf(report_id):
    from io import BytesIO
    from fpdf import FPDF

    report = db.session.get(StudentReport, report_id)
    if not report:
        abort(404)

    s = report.summary_json
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Header
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(27, 54, 93)  # navy
    pdf.cell(0, 12, 'CoachPrash', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, f'Progress Report: {s.get("student_name", "Student")}', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, f'{s.get("period_label", "")}  |  {s.get("student_email", "")}', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(8)

    # Stats row
    pdf.set_draw_color(200, 200, 200)
    stats = [
        ('Attempts', str(s.get('attempts', 0))),
        ('Accuracy', f'{s.get("accuracy", 0)}%'),
        ('Concepts Touched', str(s.get('concepts_started', 0))),
        ('Completed', str(s.get('concepts_completed', 0))),
    ]
    col_w = (pdf.w - 20) / 4
    for label, value in stats:
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.set_fill_color(244, 246, 250)
        pdf.rect(x, y, col_w, 22, style='F')
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(27, 54, 93)
        pdf.set_xy(x, y + 2)
        pdf.cell(col_w, 10, value, align='C')
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(x, y + 12)
        pdf.cell(col_w, 8, label, align='C')
        pdf.set_xy(x + col_w, y)
    pdf.ln(28)

    # Accuracy trend
    if s.get('prev_accuracy') is not None:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(27, 54, 93)
        pdf.cell(0, 10, 'Accuracy Trend', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 11)
        diff = s.get('accuracy', 0) - s.get('prev_accuracy', 0)
        trend = f'+{diff:.1f}%' if diff > 0 else f'{diff:.1f}%'
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 7, f'Previous month: {s.get("prev_accuracy")}%  ->  This month: {s.get("accuracy", 0)}%  ({trend})', new_x='LMARGIN', new_y='NEXT')
        pdf.ln(4)

    def _render_topic_table(title, topics, color_rgb):
        if not topics:
            return
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(27, 54, 93)
        pdf.cell(0, 10, title, new_x='LMARGIN', new_y='NEXT')
        # Table header
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(27, 54, 93)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(90, 8, 'Topic', fill=True)
        pdf.cell(40, 8, 'Accuracy', fill=True)
        pdf.cell(40, 8, 'Problems', fill=True, new_x='LMARGIN', new_y='NEXT')
        # Rows
        pdf.set_font('Helvetica', '', 10)
        for t in topics:
            pdf.set_text_color(60, 60, 60)
            pdf.cell(90, 7, t.get('name', ''))
            pdf.set_text_color(*color_rgb)
            pdf.cell(40, 7, f'{t.get("accuracy", 0)}%')
            pdf.set_text_color(60, 60, 60)
            pdf.cell(40, 7, str(t.get('total', 0)), new_x='LMARGIN', new_y='NEXT')
        pdf.ln(4)

    _render_topic_table('Strongest Topics', s.get('strongest', []), (40, 167, 69))
    _render_topic_table('Areas for Improvement', s.get('weakest', []), (220, 53, 69))

    # Recommendations
    recs = s.get('recommendations', [])
    if recs:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(27, 54, 93)
        pdf.cell(0, 10, 'Recommendations', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        for rec in recs:
            pdf.cell(6, 6, chr(8226))
            pdf.cell(0, 6, f' {rec}', new_x='LMARGIN', new_y='NEXT')
        pdf.ln(4)

    # Footer
    pdf.ln(8)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(4)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, 'Generated by CoachPrash', align='C')

    pdf_buffer = BytesIO(pdf.output())

    from flask import send_file
    filename = f'report_{s.get("student_name", "student")}_{report.report_month}_{report.report_year}.pdf'
    logger.info('PDF report downloaded: %s', filename)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)


# --- What's New (Changelog) ---

@admin_bp.route('/changelog')
@admin_required
def changelog():
    return render_template('admin/changelog.html')


# --- Theme Management ---

@admin_bp.route('/themes')
@admin_required
def manage_themes():
    themes = Theme.query.order_by(Theme.display_order).all()
    theme_data = []
    for t in themes:
        user_count = User.query.filter_by(theme_id=t.id).count()
        theme_data.append({'theme': t, 'user_count': user_count})
    return render_template('admin/manage_themes.html', theme_data=theme_data)


@admin_bp.route('/themes/new', methods=['GET', 'POST'])
@admin_required
def new_theme():
    form = ThemeForm()
    if form.validate_on_submit():
        max_order = db.session.query(db.func.max(Theme.display_order)).scalar() or 0
        theme = Theme(
            name=form.name.data.strip(),
            color_primary=form.color_primary.data.upper(),
            color_secondary=form.color_secondary.data.upper(),
            color_accent=form.color_accent.data.upper(),
            color_bg=form.color_bg.data.upper(),
            is_active=form.is_active.data,
            display_order=max_order + 1,
        )
        db.session.add(theme)
        db.session.commit()
        logger.info('Theme created: %s', theme.name)
        flash(f'Theme "{theme.name}" created.', 'success')
        return redirect(url_for('admin_panel.manage_themes'))
    return render_template('admin/theme_form.html', form=form, editing=False)


@admin_bp.route('/themes/<theme_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_theme(theme_id):
    theme = db.session.get(Theme, theme_id)
    if not theme:
        abort(404)
    form = ThemeForm(obj=theme)
    if form.validate_on_submit():
        theme.name = form.name.data.strip()
        theme.color_primary = form.color_primary.data.upper()
        theme.color_secondary = form.color_secondary.data.upper()
        theme.color_accent = form.color_accent.data.upper()
        theme.color_bg = form.color_bg.data.upper()
        theme.is_active = form.is_active.data
        db.session.commit()
        logger.info('Theme updated: %s', theme.name)
        flash(f'Theme "{theme.name}" updated.', 'success')
        return redirect(url_for('admin_panel.manage_themes'))
    return render_template('admin/theme_form.html', form=form, editing=True, theme=theme)


@admin_bp.route('/themes/<theme_id>/delete', methods=['POST'])
@admin_required
def delete_theme(theme_id):
    theme = db.session.get(Theme, theme_id)
    if not theme:
        abort(404)
    if theme.is_default:
        flash('Cannot delete the default theme.', 'danger')
        return redirect(url_for('admin_panel.manage_themes'))
    user_count = User.query.filter_by(theme_id=theme.id).count()
    if user_count > 0:
        User.query.filter_by(theme_id=theme.id).update({'theme_id': None})
    db.session.delete(theme)
    db.session.commit()
    logger.info('Theme deleted: %s (reassigned %d users)', theme.name, user_count)
    flash(f'Theme "{theme.name}" deleted. {user_count} user(s) reset to default.', 'success')
    return redirect(url_for('admin_panel.manage_themes'))


@admin_bp.route('/themes/<theme_id>/set-default', methods=['POST'])
@admin_required
def set_default_theme(theme_id):
    theme = db.session.get(Theme, theme_id)
    if not theme:
        abort(404)
    Theme.query.update({'is_default': False})
    theme.is_default = True
    db.session.commit()
    logger.info('Default theme set to: %s', theme.name)
    flash(f'"{theme.name}" is now the default theme.', 'success')
    return redirect(url_for('admin_panel.manage_themes'))
