from flask import render_template
from app.blueprints.blog import blog_bp
from app.models import BlogPost


@blog_bp.route('/')
def list_posts():
    posts = BlogPost.query.filter_by(is_published=True).order_by(
        BlogPost.published_at.desc()
    ).all()
    return render_template('blog/list.html', posts=posts)


@blog_bp.route('/<slug>')
def view_post(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template('blog/post.html', post=post)
