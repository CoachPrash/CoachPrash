from flask import render_template, flash, redirect, url_for, request, Response, make_response
from app.blueprints.main import main_bp
from app.blueprints.main.forms import ContactForm
from app.models import Testimonial, ContactMessage, BlogPost
from app.extensions import db, limiter


@main_bp.route('/')
def home():
    from app.models.content import Subject
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.display_order).all()
    testimonials = Testimonial.query.filter_by(is_active=True, is_featured=True).limit(3).all()
    if len(testimonials) < 3:
        testimonials = Testimonial.query.filter_by(is_active=True).limit(3).all()
    return render_template('main/home.html', subjects=subjects, testimonials=testimonials)


@main_bp.route('/about')
def about():
    from app.models.content import Subject
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.display_order).all()
    return render_template('main/about.html', subjects=subjects)


@main_bp.route('/contact', methods=['GET', 'POST'])
@limiter.limit('2/minute', methods=['POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data,
        )
        db.session.add(message)
        db.session.commit()
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('main/contact.html', form=form)


@main_bp.route('/testimonials')
def testimonials():
    all_testimonials = Testimonial.query.filter_by(is_active=True).order_by(
        Testimonial.is_featured.desc(), Testimonial.created_at.desc()
    ).all()
    return render_template('main/testimonials.html', testimonials=all_testimonials)


@main_bp.route('/robots.txt')
def robots_txt():
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /api/',
        'Disallow: /progress/',
        'Disallow: /auth/',
        '',
        f'Sitemap: {request.url_root.rstrip("/")}sitemap.xml',
    ]
    return Response('\n'.join(lines), mimetype='text/plain')


@main_bp.route('/sitemap.xml')
def sitemap_xml():
    from app.models.content import Subject, Topic, Concept
    base = request.url_root.rstrip('/')
    pages = []

    # Static pages
    for endpoint in ['main.home', 'main.about', 'main.contact', 'main.testimonials']:
        pages.append({'loc': base + url_for(endpoint), 'priority': '0.8'})

    # Subjects
    subjects = Subject.query.filter_by(is_active=True).all()
    for subject in subjects:
        pages.append({
            'loc': base + url_for('subjects.subject_detail', slug=subject.slug),
            'priority': '0.7',
        })
        # Topics
        topics = Topic.query.filter_by(subject_id=subject.id, is_active=True).all()
        for topic in topics:
            pages.append({
                'loc': base + url_for('subjects.topic_detail',
                                      subject_slug=subject.slug, topic_slug=topic.slug),
                'priority': '0.6',
            })
            # Free concepts only
            concepts = Concept.query.filter_by(
                topic_id=topic.id, is_active=True, access_tier='free'
            ).all()
            for concept in concepts:
                pages.append({
                    'loc': base + url_for('subjects.concept_detail',
                                          subject_slug=subject.slug,
                                          topic_slug=topic.slug,
                                          concept_slug=concept.slug),
                    'priority': '0.5',
                })

    # Blog posts
    posts = BlogPost.query.filter_by(is_published=True).all()
    for post in posts:
        pages.append({
            'loc': base + url_for('blog.view_post', slug=post.slug),
            'priority': '0.5',
        })

    xml = render_template('sitemap.xml', pages=pages)
    resp = make_response(xml)
    resp.headers['Content-Type'] = 'application/xml'
    return resp
