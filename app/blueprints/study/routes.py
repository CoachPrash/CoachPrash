from flask import render_template
from app.blueprints.study import study_bp


@study_bp.route('/progress/')
def progress_dashboard():
    return render_template('study/coming_soon.html', subject=None, topic=None, concepts=[])
