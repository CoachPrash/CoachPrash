import logging
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.theme import Theme
from app.utils.colors import derive_palette
from app.blueprints.settings import settings_bp

logger = logging.getLogger(__name__)


@settings_bp.route('/')
@login_required
def index():
    return redirect(url_for('settings.theme_picker'))


@settings_bp.route('/theme', methods=['GET', 'POST'])
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
