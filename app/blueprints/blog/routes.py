from flask import render_template, request
from app.blueprints.blog import blog_bp
from app.models import BlogPost


@blog_bp.route('/')
def list_posts():
    page = request.args.get('page', 1, type=int)
    pagination = BlogPost.query.filter_by(is_published=True).order_by(
        BlogPost.published_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    return render_template('blog/list.html', posts=pagination.items, pagination=pagination)


@blog_bp.route('/<slug>')
def view_post(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template('blog/post.html', post=post)
