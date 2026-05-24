import logging
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, logout_user
from app.extensions import db, limiter
from app.models.theme import Theme
from app.utils.colors import derive_palette
from app.blueprints.settings import settings_bp

logger = logging.getLogger(__name__)


# --- Account Deletion (GDPR "right to be forgotten") ---

@settings_bp.route('/delete-account', methods=['POST'])
@limiter.limit("2/hour")
@login_required
def delete_account():
    if current_user.is_admin:
        flash('Admin accounts cannot be self-deleted.', 'danger')
        return redirect(url_for('settings.theme_picker'))

    confirm = request.form.get('confirm_delete', '').strip()
    if confirm != current_user.email:
        flash('Please type your email to confirm account deletion.', 'danger')
        return redirect(url_for('settings.theme_picker'))

    user_id = current_user.id
    username = current_user.username
    logger.warning('Account deletion requested by user %s (id=%s)', username, user_id)

    # Remove related data
    from app.models.progress import StudentProgress, AttemptLog
    from app.models.messaging import MessageParticipant, Message
    from app.models.parent import ParentStudentLink, ParentLinkCode

    AttemptLog.query.filter_by(student_id=user_id).delete()
    StudentProgress.query.filter_by(student_id=user_id).delete()
    Message.query.filter_by(sender_id=user_id).delete()
    MessageParticipant.query.filter_by(user_id=user_id).delete()
    ParentStudentLink.query.filter(
        (ParentStudentLink.parent_id == user_id) | (ParentStudentLink.student_id == user_id)
    ).delete(synchronize_session=False)
    ParentLinkCode.query.filter_by(student_id=user_id).delete()

    from app.models.user import User
    user = db.session.get(User, user_id)
    logout_user()
    db.session.delete(user)
    db.session.commit()

    logger.warning('Account deleted: %s (id=%s)', username, user_id)
    flash('Your account and all associated data have been permanently deleted.', 'info')
    return redirect(url_for('main.home'))


# --- Data Export (GDPR "right to access") ---

@settings_bp.route('/export-data')
@limiter.limit("3/hour")
@login_required
def export_data():
    from app.models.progress import StudentProgress, AttemptLog

    data = {
        'account': {
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role,
            'tier': current_user.tier,
            'created_at': str(current_user.created_at),
        },
        'progress': [
            {
                'topic_id': p.topic_id,
                'problems_attempted': p.problems_attempted,
                'problems_correct': p.problems_correct,
                'updated_at': str(p.updated_at),
            }
            for p in StudentProgress.query.filter_by(student_id=current_user.id).all()
        ],
        'attempts': [
            {
                'problem_id': a.problem_id,
                'submitted_answer': a.submitted_answer,
                'is_correct': a.is_correct,
                'created_at': str(a.created_at),
            }
            for a in AttemptLog.query.filter_by(student_id=current_user.id).order_by(
                AttemptLog.created_at.desc()
            ).limit(1000).all()
        ],
    }

    response = jsonify(data)
    response.headers['Content-Disposition'] = f'attachment; filename=coachprash_data_{current_user.username}.json'
    return response


@settings_bp.route('/')
@login_required
def index():
    return redirect(url_for('settings.theme_picker'))


@settings_bp.route('/theme', methods=['GET', 'POST'])
@limiter.limit("10/minute", methods=["POST"])
@login_required
def theme_picker():
    if request.method == 'POST':
        theme_id = request.form.get('theme_id', '').strip()
        if theme_id:
            theme = Theme.query.filter_by(id=theme_id, is_active=True).first()
            if theme:
                current_user.theme_id = theme.id
                db.session.commit()
                flash(f'Theme changed to {theme.name}.', 'success')
                logger.info('User %s changed theme to %s', current_user.username, theme.name)
        return redirect(url_for('settings.theme_picker'))

    themes = Theme.query.filter_by(is_active=True).order_by(Theme.display_order).all()
    theme_previews = []
    for t in themes:
        palette = derive_palette(t.color_primary, t.color_secondary, t.color_accent, t.color_bg)
        theme_previews.append({'theme': t, 'palette': palette})

    return render_template('settings/theme.html', theme_previews=theme_previews)
