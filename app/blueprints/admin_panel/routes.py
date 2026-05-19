import json
import logging
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask import render_template, flash, redirect, url_for, request, abort, jsonify
from flask_login import login_required, current_user
from app.blueprints.admin_panel import admin_bp
from app.blueprints.admin_panel.forms import (
    StudentEditForm, SubjectForm, TopicForm, ConceptForm,
    ProblemSetForm, ProblemForm, AccessCodeForm, BlogPostForm, TestimonialForm,
    ResourceForm,
)
from app.models import (
    Testimonial, BlogPost, ContactMessage, Resource,
)
from app.models.user import User
from app.models.content import Subject, Topic, Concept
from app.models.practice import ProblemSet, Problem, Choice, Hint, StepByStepSolution
from app.models.progress import AttemptLog
from app.models.access import AccessCode
from app.models.parent import ParentStudentLink, ParentLinkCode
from app.models.reports import StudentReport
from app.utils.progress import compute_student_stats
from app.extensions import db
from app.utils.sanitize import sanitize_html

logger = logging.getLogger(__name__)


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
        logger.info('Topic created: %s in %s', topic.name, subject.name)
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
            topic_id=topic.id,
            title=form.title.data,
            slug=form.slug.data,
            content_raw=form.content_raw.data or '',
            content_html=sanitize_html(form.content_raw.data or ''),
            estimated_minutes=form.estimated_minutes.data,
            access_tier=form.access_tier.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        db.session.add(concept)
        db.session.commit()
        logger.info('Concept created: %s in %s', concept.title, topic.name)
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
        concept.content_html = sanitize_html(form.content_raw.data or '')
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
    logger.info('Concept deleted: %s (id=%s)', concept.title, concept.id)
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
    topics = Topic.query.order_by(Topic.display_order).all()
    return render_template(
        'admin/manage_resources.html',
        resources=resources, subjects=subjects, topics=topics,
    )


@admin_bp.route('/resources/new', methods=['GET', 'POST'])
@admin_required
def new_resource():
    form = ResourceForm()
    subjects = Subject.query.order_by(Subject.display_order).all()
    topics = Topic.query.order_by(Topic.display_order).all()

    if form.validate_on_submit():
        topic_id = request.form.get('topic_id') or None
        subject_id = request.form.get('subject_id') or None
        if not topic_id and not subject_id:
            flash('Select a topic or subject to attach this resource to.', 'danger')
            return render_template(
                'admin/resource_form.html', form=form, title='New Resource',
                subjects=subjects, topics=topics,
            )

        embed_url = Resource.to_embed_url(form.url.data)
        resource = Resource(
            topic_id=topic_id,
            subject_id=subject_id,
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
        subjects=subjects, topics=topics,
    )


@admin_bp.route('/resources/<resource_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if not resource:
        abort(404)
    form = ResourceForm(obj=resource)
    subjects = Subject.query.order_by(Subject.display_order).all()
    topics = Topic.query.order_by(Topic.display_order).all()

    if form.validate_on_submit():
        topic_id = request.form.get('topic_id') or None
        subject_id = request.form.get('subject_id') or None
        if not topic_id and not subject_id:
            flash('Select a topic or subject to attach this resource to.', 'danger')
            return render_template(
                'admin/resource_form.html', form=form, title=f'Edit Resource: {resource.title}',
                subjects=subjects, topics=topics, resource=resource,
            )

        resource.topic_id = topic_id
        resource.subject_id = subject_id
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
        subjects=subjects, topics=topics, resource=resource,
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

    uploaded_key = None
    error = None

    if request.method == 'POST':
        file = request.files.get('image')
        if not file or not file.filename:
            error = 'No file selected.'
        else:
            subject_slug = request.form.get('subject_slug', 'general')
            topic_slug = request.form.get('topic_slug', 'general')
            filename = file.filename.replace(' ', '-')
            bucket_key = f'images/{subject_slug}/{topic_slug}/{filename}'
            try:
                upload_file(file, bucket_key, content_type=file.content_type)
                uploaded_key = bucket_key
                logger.info('Image uploaded: %s', bucket_key)
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

    subjects = Subject.query.order_by(Subject.display_order).all()
    topics = Topic.query.order_by(Topic.display_order).all()

    return render_template(
        'admin/upload_image.html',
        uploaded_key=uploaded_key, error=error, images=images,
        subjects=subjects, topics=topics,
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
    if not data.get('topic_slug'):
        errors.append('Missing topic_slug')

    concepts = data.get('concepts', [])
    if not concepts:
        errors.append('No concepts found')

    for ci, c in enumerate(concepts):
        if not c.get('title'):
            errors.append(f'Concept {ci + 1}: missing title')
        for psi, ps in enumerate(c.get('problem_sets', [])):
            for pi, p in enumerate(ps.get('problems', [])):
                ptype = p.get('problem_type', 'mcq')
                if ptype not in ('mcq', 'fill_in_blank', 'frq'):
                    errors.append(f'Concept {ci + 1}, Problem Set {psi + 1}, Problem {pi + 1}: invalid problem_type "{ptype}"')
                if ptype == 'mcq' and not p.get('choices'):
                    errors.append(f'Concept {ci + 1}, PS {psi + 1}, Problem {pi + 1}: MCQ missing choices')
                if ptype == 'fill_in_blank' and not p.get('correct_answer'):
                    errors.append(f'Concept {ci + 1}, PS {psi + 1}, Problem {pi + 1}: fill_in_blank missing correct_answer')

    if errors:
        return jsonify({'valid': False, 'errors': errors})

    # Check subject/topic exist
    subject = Subject.query.filter_by(slug=data['subject_slug']).first()
    if not subject:
        return jsonify({'valid': False, 'error': f'Subject "{data["subject_slug"]}" not found in DB.'})
    topic = Topic.query.filter_by(subject_id=subject.id, slug=data['topic_slug']).first()
    if not topic:
        return jsonify({'valid': False, 'error': f'Topic "{data["topic_slug"]}" not found in {subject.name}.'})

    summary = f'{len(concepts)} concept(s)'
    total_problems = sum(
        len(ps.get('problems', []))
        for c in concepts
        for ps in c.get('problem_sets', [])
    )
    summary += f', {total_problems} problem(s)'
    return jsonify({'valid': True, 'summary': summary, 'subject': subject.name, 'topic': topic.name})


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
    topic_slug = data.get('topic_slug')
    if not subject_slug or not topic_slug:
        flash('JSON must include subject_slug and topic_slug.', 'danger')
        return render_template('admin/bulk_import.html')

    subject = Subject.query.filter_by(slug=subject_slug).first()
    if not subject:
        flash(f'Subject "{subject_slug}" not found.', 'danger')
        return render_template('admin/bulk_import.html')

    topic = Topic.query.filter_by(subject_id=subject.id, slug=topic_slug).first()
    if not topic:
        flash(f'Topic "{topic_slug}" not found in {subject.name}.', 'danger')
        return render_template('admin/bulk_import.html')

    concepts_data = data.get('concepts', [])
    if not concepts_data:
        flash('No concepts found in JSON.', 'danger')
        return render_template('admin/bulk_import.html')

    # Import within a transaction
    counts = {'concepts': 0, 'problem_sets': 0, 'problems': 0, 'choices': 0, 'hints': 0, 'solutions': 0}
    try:
        for ci, cdata in enumerate(concepts_data):
            concept = Concept(
                topic_id=topic.id,
                title=cdata.get('title', f'Concept {ci + 1}'),
                slug=cdata.get('slug', cdata.get('title', f'concept-{ci + 1}').lower().replace(' ', '-')),
                content_html=sanitize_html(cdata.get('content_html', cdata.get('content_raw', ''))),
                content_raw=cdata.get('content_raw', ''),
                estimated_minutes=cdata.get('estimated_minutes', 5),
                access_tier=cdata.get('access_tier', 'free'),
                display_order=cdata.get('display_order', ci),
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
                    problem = Problem(
                        problem_set_id=ps.id,
                        question_html=sanitize_html(pdata.get('question_html', pdata.get('question_raw', ''))),
                        question_raw=pdata.get('question_raw', ''),
                        problem_type=pdata.get('problem_type', 'mcq'),
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

        db.session.commit()
        logger.info('Bulk import successful: %s concepts, %s problems, %s solutions into %s/%s',
                    counts['concepts'], counts['problems'], counts['solutions'],
                    subject.name, topic.name)
        flash(
            f"Import successful: {counts['concepts']} concepts, {counts['problem_sets']} problem sets, "
            f"{counts['problems']} problems, {counts['choices']} choices, {counts['hints']} hints, "
            f"{counts['solutions']} solutions.",
            'success'
        )
    except Exception as e:
        db.session.rollback()
        logger.exception('Bulk import failed for %s/%s', subject_slug, topic_slug)
        flash(f'Import failed: {e}', 'danger')

    return redirect(url_for('admin_panel.bulk_import'))


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
    from app.models.content import Concept, Topic, Subject
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
                topic = db.session.get(Topic, concept.topic_id)
                if topic:
                    key = topic.id
                    if key not in topic_data:
                        topic_data[key] = {'name': topic.name, 'total': 0, 'correct': 0}
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
    from xhtml2pdf import pisa

    report = db.session.get(StudentReport, report_id)
    if not report:
        abort(404)

    html = render_template('admin/report_pdf.html', report=report)
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)
    pdf_buffer.seek(0)

    from flask import send_file
    filename = f'report_{report.summary_json.get("student_name", "student")}_{report.report_month}_{report.report_year}.pdf'
    logger.info('PDF report downloaded: %s', filename)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)


# --- What's New (Changelog) ---

@admin_bp.route('/changelog')
@admin_required
def changelog():
    return render_template('admin/changelog.html')
