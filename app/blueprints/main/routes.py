from flask import render_template, flash, redirect, url_for
from app.blueprints.main import main_bp
from app.blueprints.main.forms import ContactForm
from app.models import Testimonial, ContactMessage
from app.extensions import db


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
