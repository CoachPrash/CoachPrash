from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm, RegisterForm
from app.models.user import User
from app.models.access import AccessCode
from app.extensions import db, oauth


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email.ilike(form.email.data)).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form)
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('main.home'))
        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegisterForm()
    if form.validate_on_submit():
        tier = 'free'
        access_code_obj = None

        if form.access_code.data:
            access_code_obj = AccessCode.query.filter_by(code=form.access_code.data.upper()).first()
            if not access_code_obj or not access_code_obj.is_valid():
                flash('Invalid or expired access code.', 'danger')
                return render_template('auth/register.html', form=form)
            tier = access_code_obj.tier

        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            tier=tier,
        )
        user.set_password(form.password.data)
        db.session.add(user)

        if access_code_obj:
            access_code_obj.use()

        db.session.commit()
        login_user(user)
        flash('Welcome! Your account has been created.', 'success')
        return redirect(url_for('main.home'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get('userinfo')
    if not userinfo:
        flash('Could not retrieve your Google account info.', 'danger')
        return redirect(url_for('auth.login'))

    google_id = userinfo['sub']
    email = userinfo['email'].lower()
    name = userinfo.get('name', email.split('@')[0])

    # 1) Already linked — just log in
    user = User.query.filter_by(google_id=google_id).first()
    if user:
        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=True)
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('main.home'))

    # 2) Same email exists — merge accounts (case-insensitive)
    user = User.query.filter(User.email.ilike(email)).first()
    if user:
        user.google_id = google_id
        if user.auth_provider == 'local':
            user.auth_provider = 'both'
        db.session.commit()
        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=True)
        flash(f'Welcome back, {user.username}! Your Google account is now linked.', 'success')
        return redirect(url_for('main.home'))

    # 3) Brand new user — create account
    base_username = name.replace(' ', '').lower()[:70]
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f'{base_username}{counter}'
        counter += 1

    user = User(
        email=email,
        username=username,
        google_id=google_id,
        auth_provider='google',
        tier='free',
    )
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    flash('Welcome! Your account has been created with Google.', 'success')
    return redirect(url_for('main.home'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))
